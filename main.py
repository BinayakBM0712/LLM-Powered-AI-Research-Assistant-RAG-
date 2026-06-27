import os
import uuid
import json
import shutil
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("rag_backend")

app = FastAPI(title="Gemini Research Assistant RAG API", version="1.0.0")

# Enable CORS for the React frontend (running on 5175, 5173, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local development simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Imports from internal src components
try:
    from src.ingestion.pdf_loader import load_pdf
    from src.ingestion.docx_loader import load_docx
    from src.ingestion.txt_loader import load_txt
    from src.preprocessing.chunking import split_documents
    from src.embeddings.embedding_manager import get_embedding_model
    from src.vectorstore.faiss_manager import create_vector_store, save_vector_store, load_vector_store
    from src.pipeline.rag_pipeline import run_rag_pipeline
except ImportError as e:
    logger.error(f"Failed to import internal source modules: {str(e)}")
    raise RuntimeError(f"Internal imports failed: {str(e)}")

# Constants
UPLOAD_DIR = os.path.abspath("data/uploads")
VECTOR_INDEX_DIR = os.path.abspath("vectorstore/default_index")
REGISTRY_FILE = os.path.abspath("data/registry.json")
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(VECTOR_INDEX_DIR), exist_ok=True)

# Helper: Load registry of processed files
def load_registry() -> List[str]:
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading registry: {e}")
            return []
    return []

# Helper: Save registry of processed files
def save_registry(files: List[str]):
    try:
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(files, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving registry: {e}")

# In-memory vector database reference (lazy-loaded or cached)
global_vector_db = None

def get_db(api_key: str):
    global global_vector_db
    if global_vector_db is not None:
        return global_vector_db
    
    # Try loading from disk
    if os.path.exists(VECTOR_INDEX_DIR):
        try:
            embeds = get_embedding_model(google_api_key=api_key)
            loaded_db = load_vector_store(VECTOR_INDEX_DIR, embeds)
            if loaded_db:
                global_vector_db = loaded_db
                logger.info("Loaded FAISS index from disk.")
                return global_vector_db
        except Exception as e:
            logger.warning(f"Could not load pre-existing vector store: {e}")
    return None

class QueryRequest(BaseModel):
    question: str
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.0
    top_k: int = 4

@app.get("/api/config")
async def get_config(authorization: Optional[str] = Header(None)):
    # Check key from env or header
    env_key = os.getenv("GOOGLE_API_KEY", "")
    header_key = ""
    if authorization and authorization.startswith("Bearer "):
        header_key = authorization.split(" ")[1]
    
    has_key = bool(env_key or header_key)
    return {
        "has_key": has_key,
        "env_key_available": bool(env_key)
    }

@app.get("/api/documents")
async def get_documents():
    return {"documents": load_registry()}

@app.post("/api/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    authorization: Optional[str] = Header(None)
):
    global global_vector_db
    
    # Resolve API Key
    env_key = os.getenv("GOOGLE_API_KEY", "")
    header_key = ""
    if authorization and authorization.startswith("Bearer "):
        header_key = authorization.split(" ")[1]
    
    api_key = header_key if header_key else env_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gemini API Key is missing. Please configure it in your environment or send it in the Authorization header."
        )
        
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
        
    new_docs = []
    registry = load_registry()
    processed_count = 0
    
    for file in files:
        original_name = file.filename
        ext = original_name.split(".")[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            logger.warning(f"Skipping unsupported file extension: {original_name}")
            continue
            
        # Read and check size
        file_bytes = await file.read()
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            logger.warning(f"Skipping large file: {original_name} ({file_size_mb:.2f}MB)")
            continue
            
        # Save temporary file with UUID
        secure_filename = f"{uuid.uuid4().hex}.{ext}"
        target_path = os.path.join(UPLOAD_DIR, secure_filename)
        
        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.error(f"Failed to write file {original_name}: {e}")
            continue
            
        # Parse document content
        try:
            parsed_docs = []
            if ext == "pdf":
                parsed_docs = load_pdf(target_path)
            elif ext == "docx":
                parsed_docs = load_docx(target_path)
            elif ext == "txt":
                parsed_docs = load_txt(target_path)
                
            # Keep original filename in metadata
            for doc in parsed_docs:
                doc.metadata["source"] = original_name
                
            new_docs.extend(parsed_docs)
            registry.append(original_name)
            processed_count += 1
        except Exception as e:
            logger.error(f"Failed to process file {original_name}: {e}")
            if os.path.exists(target_path):
                os.unlink(target_path)
            continue
            
    if new_docs:
        try:
            chunks = split_documents(new_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            embeds = get_embedding_model(google_api_key=api_key)
            
            db = get_db(api_key)
            if db is None:
                db = create_vector_store(chunks, embeds)
            else:
                db.add_documents(chunks)
                
            global_vector_db = db
            save_vector_store(db, VECTOR_INDEX_DIR)
            save_registry(registry)
            
            return {
                "success": True,
                "message": f"Successfully indexed {processed_count} file(s) into {len(chunks)} chunks.",
                "chunks_count": len(chunks),
                "documents": list(set(registry))
            }
        except Exception as e:
            logger.error(f"Failed to index documents into vector store: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to index documents: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="No valid documents were successfully processed.")

@app.post("/api/query")
async def query_rag(request: QueryRequest, authorization: Optional[str] = Header(None)):
    # Resolve API Key
    env_key = os.getenv("GOOGLE_API_KEY", "")
    header_key = ""
    if authorization and authorization.startswith("Bearer "):
        header_key = authorization.split(" ")[1]
        
    api_key = header_key if header_key else env_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gemini API Key is missing. Please configure it in your environment or send it in the Authorization header."
        )
        
    db = get_db(api_key)
    if db is None:
        raise HTTPException(
            status_code=400,
            detail="Vector database is empty. Please upload and process documents before querying."
        )
        
    try:
        response = run_rag_pipeline(
            db=db,
            question=request.question,
            google_api_key=api_key,
            model_name=request.model_name,
            top_k=request.top_k,
            temperature=request.temperature
        )
        
        # Serialize LangChain documents into standard JSON serializable formats
        serialized_chunks = []
        for doc in response.get("retrieved_chunks", []):
            serialized_chunks.append({
                "page_content": doc.page_content,
                "metadata": {
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", None),
                    "similarity_score": float(doc.metadata.get("similarity_score")) if doc.metadata.get("similarity_score") is not None else None
                }
            })
            
        return {
            "answer": response.get("answer"),
            "retrieved_chunks": serialized_chunks,
            "metrics": response.get("metrics")
        }
    except Exception as e:
        logger.error(f"Error running pipeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

@app.post("/api/clear")
async def clear_data():
    global global_vector_db
    global_vector_db = None
    
    # Clear upload directory
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                
    # Clear vector store directory
    if os.path.exists(VECTOR_INDEX_DIR):
        try:
            shutil.rmtree(VECTOR_INDEX_DIR)
        except Exception as e:
            logger.error(f"Error deleting vector store folder {VECTOR_INDEX_DIR}: {e}")
            
    # Clear registry
    if os.path.exists(REGISTRY_FILE):
        try:
            os.unlink(REGISTRY_FILE)
        except Exception as e:
            logger.error(f"Error deleting registry file: {e}")
            
    return {"success": True, "message": "All workspace data cleared successfully."}

@app.get("/api/health")
async def health_check(authorization: Optional[str] = Header(None)):
    env_key = os.getenv("GOOGLE_API_KEY", "")
    header_key = ""
    if authorization and authorization.startswith("Bearer "):
        header_key = authorization.split(" ")[1]
    
    api_key = header_key if header_key else env_key
    db_available = get_db(api_key) is not None if api_key else False
    
    return {
        "status": "ok",
        "has_api_key": bool(api_key),
        "db_loaded": db_available,
        "documents_indexed": len(load_registry())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
