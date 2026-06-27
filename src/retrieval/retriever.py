import time
import logging
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Configure logging
logger = logging.getLogger(__name__)

def retrieve_context(db: FAISS, query: str, top_k: int = 4) -> Dict[str, Any]:
    """
    Performs similarity search against the FAISS vector database.
    Measures and logs latency of the search.
    
    Args:
        db (FAISS): FAISS vector store database.
        query (str): The natural language query from the user.
        top_k (int): Number of top documents to retrieve.
        
    Returns:
        Dict[str, Any]: Contains retrieved documents, latency in ms, and search parameters.
    """
    logger.info(f"Retrieving context for query: '{query}' with top_k={top_k}")
    
    if not db:
        logger.warning("No vector store instance provided for retrieval.")
        return {
            "documents": [],
            "latency_ms": 0.0,
            "parameters": {"top_k": top_k}
        }
        
    # Input validation
    if top_k <= 0:
        logger.error("top_k must be greater than 0")
        raise ValueError("top_k must be a positive integer.")
        
    start_time = time.perf_counter()
    try:
        # Search with similarity score
        # Note: FAISS distance is L2 distance, lower score = higher similarity
        docs_and_scores = db.similarity_search_with_score(query, k=top_k)
        
        # Attach the score to metadata for transparency/debugging
        documents = []
        for doc, score in docs_and_scores:
            doc.metadata["similarity_score"] = float(score)
            documents.append(doc)
            
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        logger.info(f"Retrieved {len(documents)} document chunks in {latency_ms:.2f} ms")
        
        return {
            "documents": documents,
            "latency_ms": round(latency_ms, 2),
            "parameters": {
                "top_k": top_k
            }
        }
    except Exception as e:
        logger.error(f"Error during vector database retrieval: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error during context retrieval: {str(e)}")
