import os
import uuid
import logging
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rag_app.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("rag_app")

# Set Page Config
st.set_page_config(
    page_title="AI Research Assistant - Premium RAG Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Overrides to completely transform Streamlit UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', sans-serif;
        color: #e4e6eb;
    }
    
    .stApp {
        background-color: #0d0f17;
    }
    
    /* Hide Streamlit default header, footer, and menu */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
    /* Sidebar Custom Styling */
    [data-testid="stSidebar"] {
        background-color: #07090e !important;
        border-right: 1px solid rgba(127, 0, 255, 0.15) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #ffffff;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Elegant Title Header */
    .title-container {
        padding: 2.5rem 0rem 2rem 0rem;
        background: linear-gradient(180deg, rgba(127, 0, 255, 0.05) 0%, rgba(13, 15, 23, 0) 100%);
        border-bottom: 1px solid rgba(127, 0, 255, 0.1);
        margin-bottom: 2.5rem;
        text-align: center;
        border-radius: 0 0 24px 24px;
    }
    .main-title {
        background: linear-gradient(135deg, #a044ff 0%, #e100ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3.5rem;
        margin: 0;
        letter-spacing: -1px;
    }
    .subtitle {
        color: #9ea4b0;
        font-size: 1.25rem;
        margin-top: 0.75rem;
        font-weight: 300;
    }
    
    /* Card Container */
    .ingest-card {
        background: rgba(20, 22, 33, 0.7);
        border: 1px solid rgba(127, 0, 255, 0.15);
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
    }
    .ingest-card h3 {
        margin-top: 0;
        color: #ffffff;
        font-weight: 600;
        font-size: 1.5rem;
        letter-spacing: -0.5px;
    }
    
    /* Custom Uploader Drag-Drop Area */
    [data-testid="stFileUploader"] {
        background-color: rgba(127, 0, 255, 0.02) !important;
        border: 2px dashed rgba(127, 0, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 25px !important;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploader"]:hover {
        background-color: rgba(127, 0, 255, 0.05) !important;
        border-color: rgba(225, 0, 255, 0.4) !important;
    }
    
    /* Action Buttons (Streamlit Overrides) */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #7F00FF 0%, #E100FF 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        width: 100% !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        box-shadow: 0 6px 20px rgba(127, 0, 255, 0.3) !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 25px rgba(127, 0, 255, 0.5) !important;
        background: linear-gradient(135deg, #8F1FFF 0%, #F11FFF 100%) !important;
    }
    div.stButton > button:first-child:active {
        transform: translateY(1px) !important;
    }
    
    /* Tab Buttons Custom Styling */
    button[data-baseweb="tab"] {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #8a90a0 !important;
        border-bottom: 2px solid transparent !important;
        padding: 12px 24px !important;
        transition: all 0.2s ease !important;
        background-color: transparent !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #ffffff !important;
    }
    button[aria-selected="true"] {
        color: #e100ff !important;
        border-bottom: 2px solid #e100ff !important;
    }
    
    /* Metric Card Styling */
    .metric-container {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
        margin-top: 15px;
    }
    .metric-card {
        flex: 1;
        background: linear-gradient(135deg, rgba(20, 22, 33, 0.9) 0%, rgba(28, 30, 46, 0.9) 100%);
        border: 1px solid rgba(127, 0, 255, 0.15);
        border-radius: 16px;
        padding: 24px 18px;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 8px 30px rgba(0,0,0,0.25);
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(225, 0, 255, 0.4);
        box-shadow: 0 12px 35px rgba(127, 0, 255, 0.2);
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #e100ff;
        margin-bottom: 6px;
        letter-spacing: -0.5px;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #9ea4b0;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 600;
    }
    
    /* Chat bubbles */
    .chat-bubble-user {
        background: rgba(127, 0, 255, 0.1);
        border: 1px solid rgba(127, 0, 255, 0.25);
        border-radius: 20px 20px 4px 20px;
        padding: 18px 24px;
        margin: 15px 0 15px auto;
        max-width: 80%;
        color: #ffffff;
        font-size: 1.05rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    .chat-bubble-assistant {
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 20px 20px 20px 4px;
        padding: 18px 24px;
        margin: 15px 0;
        max-width: 85%;
        color: #e4e6eb;
        font-size: 1.05rem;
        line-height: 1.65;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Chat input box styling overrides */
    [data-testid="stChatInput"] {
        border-radius: 16px !important;
        border: 1px solid rgba(127, 0, 255, 0.25) !important;
        background-color: rgba(20, 22, 33, 0.8) !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        font-size: 1rem !important;
    }
    
    /* Citation/Source Cards */
    .source-chunk-card {
        background: rgba(20, 22, 33, 0.5);
        border-left: 5px solid #e100ff;
        border-top: 1px solid rgba(127, 0, 255, 0.1);
        border-right: 1px solid rgba(127, 0, 255, 0.1);
        border-bottom: 1px solid rgba(127, 0, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .source-chunk-card:hover {
        transform: translateY(-2px);
        background: rgba(20, 22, 33, 0.7);
        border-color: rgba(225, 0, 255, 0.3);
    }
    .source-meta {
        font-weight: 600;
        font-size: 0.95rem;
        color: #a044ff;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
    }
    .source-content {
        font-size: 0.95rem;
        color: #e4e6eb;
        line-height: 1.65;
        white-space: pre-wrap;
    }
    
    /* Code formatting */
    code {
        color: #e100ff !important;
        background-color: rgba(127, 0, 255, 0.08) !important;
        padding: 3px 7px;
        border-radius: 5px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Imports from src components
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
    st.error(f"Internal imports failed: {str(e)}")
    st.stop()

# Constants
UPLOAD_DIR = os.path.abspath("data/uploads")
VECTOR_INDEX_DIR = os.path.abspath("vectorstore/default_index")
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

# Ensure folders exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(VECTOR_INDEX_DIR), exist_ok=True)

# Session State Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "current_response" not in st.session_state:
    st.session_state.current_response = None

# Sidebar Controls
with st.sidebar:
    st.markdown("## ⚙️ Settings Panel")
    st.markdown("---")
    
    st.markdown("### 🔑 Gemini Credentials")
    env_api_key = os.getenv("GOOGLE_API_KEY", "")
    ui_api_key = st.text_input(
        "Gemini API Key",
        value=env_api_key if env_api_key else "",
        type="password",
        help="Paste your Google Gemini API key here. It is loaded automatically if present in .env"
    )
    resolved_api_key = ui_api_key if ui_api_key else env_api_key
    
    st.markdown("[🔗 Get Free Gemini API Key](https://aistudio.google.com/app/apikey)")
    st.markdown("---")
    
    st.markdown("### 🧠 Model Config")
    model_name = st.selectbox(
        "Model Engine",
        options=["gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help="gemini-1.5-flash is optimized for speed; gemini-1.5-pro for complex queries."
    )
    
    temperature = st.slider(
        "Temperature (Creativity)",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.1,
        help="0.0 makes the model fully deterministic and factual."
    )
    
    st.markdown("---")
    st.markdown("### 🎛️ Indexing Config")
    chunk_size = st.slider(
        "Chunk Size (Characters)",
        min_value=200,
        max_value=2000,
        value=1000,
        step=100,
        help="Target length for splitting document sections."
    )
    
    chunk_overlap = st.slider(
        "Chunk Overlap",
        min_value=0,
        max_value=500,
        value=200,
        step=50,
        help="Characters shared between adjacent segments."
    )
    
    top_k = st.slider(
        "Top-K (Retrieval Limit)",
        min_value=1,
        max_value=10,
        value=4,
        step=1,
        help="Maximum chunks sent to the model for context answers."
    )
    
    st.markdown("---")
    # Reset Application
    if st.button("🧹 Clear All Data", type="primary", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.processed_files = []
        st.session_state.vector_db = None
        st.session_state.current_response = None
        
        # Clear upload directory files
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")
                
        # Clear vectorstore index
        import shutil
        if os.path.exists(VECTOR_INDEX_DIR):
            try:
                shutil.rmtree(VECTOR_INDEX_DIR)
            except Exception as e:
                logger.error(f"Error deleting vector store folder {VECTOR_INDEX_DIR}: {e}")
                
        st.success("App data cleared successfully!")
        st.rerun()

# Main Container header
st.markdown("""
<div class="title-container">
    <h1 class="main-title">🎓 Gemini Research Assistant</h1>
    <div class="subtitle">An enterprise-grade Retrieval-Augmented Generation (RAG) dashboard to query research papers.</div>
</div>
""", unsafe_allow_html=True)

# Try loading vector store on startup if it exists and session is empty
if st.session_state.vector_db is None and resolved_api_key:
    try:
        embeds = get_embedding_model(google_api_key=resolved_api_key)
        loaded_db = load_vector_store(VECTOR_INDEX_DIR, embeds)
        if loaded_db:
            st.session_state.vector_db = loaded_db
            logger.info("Loaded pre-existing FAISS vector store on startup.")
    except Exception as e:
        logger.warning(f"Did not load pre-existing vector store: {e}")

# Application Content - 2 Columns Layout
col_left, col_right = st.columns([1, 2.2])

# Left Column - File Ingestion
with col_left:
    st.markdown('<div class="ingest-card">', unsafe_allow_html=True)
    st.markdown("### 📁 Ingestion Hub")
    st.markdown("Upload documents to generate semantic vector indexing.")
    
    if not resolved_api_key:
        st.warning("⚠️ Enter a Gemini API Key in the Settings Panel to upload.")
        
    uploaded_files = st.file_uploader(
        "Upload Papers",
        type=list(ALLOWED_EXTENSIONS),
        accept_multiple_files=True,
        disabled=not resolved_api_key,
        label_visibility="collapsed"
    )
    
    if st.button("🚀 Process Documents", use_container_width=True, disabled=not uploaded_files or not resolved_api_key):
        with st.spinner("Analyzing and indexing documents..."):
            new_docs = []
            
            for uploaded_file in uploaded_files:
                original_name = uploaded_file.name
                
                # Check extension
                ext = original_name.split(".")[-1].lower()
                if ext not in ALLOWED_EXTENSIONS:
                    st.error(f"Skipping {original_name}: File type not supported.")
                    continue
                    
                # Validate File Size
                file_bytes = uploaded_file.read()
                file_size_mb = len(file_bytes) / (1024 * 1024)
                if file_size_mb > MAX_FILE_SIZE_MB:
                    st.error(f"Skipping {original_name}: File exceeds {MAX_FILE_SIZE_MB}MB size limit.")
                    continue
                    
                # Generate unique filename for upload directory
                secure_filename = f"{uuid.uuid4().hex}.{ext}"
                target_path = os.path.join(UPLOAD_DIR, secure_filename)
                
                # Write to disk safely
                try:
                    with open(target_path, "wb") as f:
                        f.write(file_bytes)
                except Exception as e:
                    logger.error(f"Failed to write file {original_name}: {e}")
                    st.error(f"Error saving file {original_name}.")
                    continue
                
                # Parse Document
                try:
                    parsed_docs = []
                    if ext == "pdf":
                        parsed_docs = load_pdf(target_path)
                    elif ext == "docx":
                        parsed_docs = load_docx(target_path)
                    elif ext == "txt":
                        parsed_docs = load_txt(target_path)
                        
                    # Override document metadata source so it displays original name, not UUID path
                    for doc in parsed_docs:
                        doc.metadata["source"] = original_name
                        
                    new_docs.extend(parsed_docs)
                    st.session_state.processed_files.append(original_name)
                    
                except Exception as e:
                    logger.error(f"Failed to process file {original_name}: {e}")
                    st.error(f"Could not read {original_name}.")
                    if os.path.exists(target_path):
                        os.unlink(target_path)
                    continue
            
            if new_docs:
                try:
                    # Chunk documents
                    chunks = split_documents(new_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                    
                    # Generate Embeddings & Save into FAISS
                    embeds = get_embedding_model(google_api_key=resolved_api_key)
                    
                    if st.session_state.vector_db is None:
                        st.session_state.vector_db = create_vector_store(chunks, embeds)
                    else:
                        st.session_state.vector_db.add_documents(chunks)
                        
                    # Save FAISS index
                    save_vector_store(st.session_state.vector_db, VECTOR_INDEX_DIR)
                    st.success(f"Indexed {len(uploaded_files)} file(s) into {len(chunks)} chunks!")
                except Exception as e:
                    st.error(f"Failed to index documents: {str(e)}")
                    logger.error(f"Index error: {str(e)}", exc_info=True)
            else:
                st.warning("No new valid documents were found to process.")
    st.markdown('</div>', unsafe_allow_html=True)
                
    # Display processed files list
    if st.session_state.processed_files:
        st.markdown('<div class="ingest-card">', unsafe_allow_html=True)
        st.markdown("#### 📂 Active Documents")
        unique_processed = list(set(st.session_state.processed_files))
        for filename in unique_processed:
            st.caption(f"📁 {filename}")
        st.markdown('</div>', unsafe_allow_html=True)

# Right Column - Chat Panel & QA (Professional SaaS Tabs)
with col_right:
    # Set up Tabbed Workspace
    tab_chat, tab_sources, tab_metrics = st.tabs([
        "💬 Chat Playground", 
        "🔍 Inspected Sources", 
        "📊 Latency & Analytics"
    ])
    
    # 1. Chat Playground Tab
    with tab_chat:
        st.markdown("### Ask Your Research Papers")
        
        # Chat history renderer
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_history:
                for q, a in st.session_state.chat_history:
                    # Render User Message
                    st.markdown(f'<div class="chat-bubble-user">🕵️ **You**: {q}</div>', unsafe_allow_html=True)
                    # Render Assistant Message
                    st.markdown(f'<div class="chat-bubble-assistant">🤖 **Assistant**: {a}</div>', unsafe_allow_html=True)
            else:
                st.info("👋 Send a message below to start questioning your processed papers.")
        
        # Chat interface input
        user_query = st.chat_input("Ask a question about the uploaded papers...", disabled=st.session_state.vector_db is None)
        
        if user_query:
            if not resolved_api_key:
                st.error("Please enter your Gemini API Key in the Control Center sidebar.")
            else:
                with st.spinner("Retrieving facts and synthesizing response..."):
                    try:
                        # Execute RAG Pipeline
                        response = run_rag_pipeline(
                            db=st.session_state.vector_db,
                            question=user_query,
                            google_api_key=resolved_api_key,
                            model_name=model_name,
                            top_k=top_k,
                            temperature=temperature
                        )
                        
                        # Store response in session state
                        st.session_state.current_response = response
                        st.session_state.chat_history.append((user_query, response["answer"]))
                        st.rerun()
                    except Exception as e:
                        st.error(f"Pipeline error: {str(e)}")
                        logger.error(f"Pipeline execution error: {str(e)}", exc_info=True)
                        
    # 2. Inspected Sources Tab
    with tab_sources:
        st.markdown("### Retrievable Context Inspection")
        st.markdown("Examine the exact chunks and metadata retrieved for the last user question.")
        
        if st.session_state.current_response:
            res = st.session_state.current_response
            if res["retrieved_chunks"]:
                for idx, doc in enumerate(res["retrieved_chunks"]):
                    src_doc = doc.metadata.get("source", "Unknown")
                    score = doc.metadata.get("similarity_score", None)
                    score_info = f"Distance (L2): {score:.4f}" if score is not None else ""
                    page_num = doc.metadata.get("page", None)
                    page_info = f"Page: {page_num}" if page_num is not None else ""
                    
                    st.markdown(f"""
                    <div class="source-chunk-card">
                        <div class="source-meta">
                            <span>📄 Chunk {idx + 1} | {src_doc}</span>
                            <span>{page_info} {" • " + score_info if score_info else ""}</span>
                        </div>
                        <div class="source-content">{doc.page_content}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No documents retrieved. Submit a query to inspect.")
        else:
            st.info("Submit a question to view the retrieved source documents.")
            
    # 3. Performance Metrics Tab
    with tab_metrics:
        st.markdown("### Execution & Performance Analytics")
        st.markdown("Detailed breakdown of retrieval and response generation times.")
        
        if st.session_state.current_response:
            res = st.session_state.current_response
            metrics = res["metrics"]
            
            # Display Metrics Badges
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card">
                    <div class="metric-value">{metrics["retrieval_latency_ms"]} ms</div>
                    <div class="metric-label">🔍 Retrieval Latency</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics["generation_latency_ms"]} ms</div>
                    <div class="metric-label">⚡ LLM Generation Latency</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics["total_latency_ms"]} ms</div>
                    <div class="metric-label">🕒 Total Pipeline Time</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Visual Breakdown (Progress-bar format)
            ret_pct = int((metrics["retrieval_latency_ms"] / metrics["total_latency_ms"]) * 100)
            gen_pct = 100 - ret_pct
            
            st.markdown("#### Latency Percentage Share")
            st.caption(f"Retrieval: {ret_pct}% | LLM Generation: {gen_pct}%")
            
            col_bar1, col_bar2 = st.columns([ret_pct, gen_pct])
            with col_bar1:
                st.error("🔍 Retrieval Share")
            with col_bar2:
                st.success("⚡ LLM Generation Share")
                
            st.markdown("---")
            st.markdown("#### Configured Execution Parameters")
            st.code(f"""
- Model Engine: {model_name}
- Embedding Model: models/gemini-embedding-001 (auto-detected)
- Temperature (Sampling): {temperature}
- Retrieval Count (Top-K): {top_k} Chunks
- Input Chunk Size: {chunk_size} characters
- Input Chunk Overlap: {chunk_overlap} characters
- Source Documents: {", ".join(metrics["sources"])}
            """)
        else:
            st.info("Submit a question to generate execution performance logs.")
