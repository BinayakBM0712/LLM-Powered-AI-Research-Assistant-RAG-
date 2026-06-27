import os
import logging
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("verify_pipeline")

def test_pipeline():
    logger.info("Starting local pipeline sanity check for Google Gemini...")
    
    # 1. Create a temporary test file
    test_file_path = "test_doc.txt"
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("Artificial intelligence (AI) is intelligence demonstrated by machines, "
                "as opposed to natural intelligence displayed by animals including humans. "
                "Leading AI textbooks define the field as the study of 'intelligent agents': "
                "any system that perceives its environment and takes actions that maximize "
                "its chance of achieving its goals.\n\n"
                "RAG stands for Retrieval-Augmented Generation. It is a technique used to "
                "ground large language model answers in verified facts retrieved from external "
                "knowledge sources, reducing hallucination.")
    
    logger.info(f"Created temporary test document at: {test_file_path}")
    
    try:
        # 2. Test txt loader
        from src.ingestion.txt_loader import load_txt
        docs = load_txt(test_file_path)
        logger.info(f"Ingestion successful. Loaded {len(docs)} documents.")
        
        # 3. Test chunker
        from src.preprocessing.chunking import split_documents
        chunks = split_documents(docs, chunk_size=150, chunk_overlap=30)
        logger.info(f"Chunking successful. Generated {len(chunks)} chunks.")
        for i, chunk in enumerate(chunks):
            logger.info(f"Chunk {i+1} content preview: {chunk.page_content[:60]}...")
            
        # 4. Check for Google key to test embedding and FAISS
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY environment variable is not set. Skipping embeddings & FAISS test.")
            logger.info("Sanity check completed successfully for loaders and splitters!")
            return
            
        logger.info("GOOGLE_API_KEY found. Testing embeddings and FAISS index creation...")
        from src.embeddings.embedding_manager import get_embedding_model
        from src.vectorstore.faiss_manager import create_vector_store
        
        embeds = get_embedding_model(api_key)
        db = create_vector_store(chunks, embeds)
        logger.info("FAISS vector store successfully created.")
        
        # 5. Test retrieval
        from src.retrieval.retriever import retrieve_context
        retrieved = retrieve_context(db, "What does RAG stand for?", top_k=2)
        logger.info(f"Retrieval successful. Retrieved {len(retrieved['documents'])} chunks in {retrieved['latency_ms']} ms.")
        for idx, doc in enumerate(retrieved['documents']):
            logger.info(f"Retrieved chunk {idx+1}: {doc.page_content}")
            
        # 6. Test complete pipeline
        from src.pipeline.rag_pipeline import run_rag_pipeline
        response = run_rag_pipeline(db=db, question="What is RAG?", google_api_key=api_key, top_k=2)
        logger.info(f"Pipeline executed successfully. Answer:\n{response['answer']}")
        logger.info(f"Metrics: {response['metrics']}")
        
    except Exception as e:
        logger.error(f"Sanity check failed: {str(e)}", exc_info=True)
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            logger.info("Temporary test document cleaned up.")

if __name__ == "__main__":
    test_pipeline()
