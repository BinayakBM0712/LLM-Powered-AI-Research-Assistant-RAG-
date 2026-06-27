import time
import logging
from typing import Dict, Any
from langchain_community.vectorstores import FAISS
from src.retrieval.retriever import retrieve_context
from src.prompts.rag_prompt import get_rag_prompt
from src.llm.llm_manager import get_llm

# Configure logging
logger = logging.getLogger(__name__)

def run_rag_pipeline(
    db: FAISS,
    question: str,
    google_api_key: str = None,
    model_name: str = None,
    top_k: int = 4,
    temperature: float = 0.0
) -> Dict[str, Any]:
    """
    Orchestrates the Retrieval-Augmented Generation (RAG) pipeline:
    1. Retrieves similar documents from vector store.
    2. Measures retrieval latency.
    3. Builds the context string.
    4. Formulates custom prompt.
    5. Queries Google Gemini LLM.
    6. Measures response generation latency.
    7. Tracks sources and evaluation metrics.
    
    Args:
        db (FAISS): FAISS vector store database.
        question (str): The user's prompt or question.
        google_api_key (str): Optional Google Gemini API Key.
        model_name (str): Optional Gemini model name.
        top_k (int): Number of chunks to retrieve.
        temperature (float): Model temperature.
        
    Returns:
        Dict[str, Any]: Answer, source documents, and detailed execution metrics.
    """
    logger.info("Running RAG pipeline execution with Google Gemini")
    start_pipeline_time = time.perf_counter()
    
    # 1. Context Retrieval
    retrieval_res = retrieve_context(db=db, query=question, top_k=top_k)
    retrieved_docs = retrieval_res["documents"]
    retrieval_latency = retrieval_res["latency_ms"]
    
    # Extract unique source names
    sources = []
    for doc in retrieved_docs:
        source_name = doc.metadata.get("source", "Unknown")
        import os
        source_basename = os.path.basename(source_name)
        if source_basename not in sources:
            sources.append(source_basename)
            
    # 2. Context Formulation
    context_str = ""
    for idx, doc in enumerate(retrieved_docs):
        source_name = os.path.basename(doc.metadata.get("source", "Unknown"))
        page_num = doc.metadata.get("page", None)
        page_info = f", Page: {page_num}" if page_num is not None else ""
        context_str += f"[Chunk {idx+1} | Source: {source_name}{page_info}]\n{doc.page_content}\n\n"
        
    # 3. LLM Query Execution
    llm_start_time = time.perf_counter()
    
    if not retrieved_docs:
        logger.warning("No context found. Pipeline returning default empty context answer.")
        context_str = "(No document context available.)"
        
    try:
        # Get Prompt Template
        prompt_template = get_rag_prompt()
        formatted_prompt = prompt_template.format(context=context_str, question=question)
        
        # Initialize LLM
        llm = get_llm(
            google_api_key=google_api_key,
            model_name=model_name,
            temperature=temperature
        )
        
        # Invoke LLM
        response = llm.invoke(formatted_prompt)
        answer = response.content
        
        llm_end_time = time.perf_counter()
        generation_latency = (llm_end_time - llm_start_time) * 1000
        total_latency = (llm_end_time - start_pipeline_time) * 1000
        
        logger.info(f"RAG pipeline completed successfully in {total_latency:.2f} ms")
        
        return {
            "answer": answer,
            "retrieved_chunks": retrieved_docs,
            "metrics": {
                "retrieval_latency_ms": round(retrieval_latency, 2),
                "generation_latency_ms": round(generation_latency, 2),
                "total_latency_ms": round(total_latency, 2),
                "num_chunks_retrieved": len(retrieved_docs),
                "sources": sources
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing LLM response generation in pipeline: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error generating answer: {str(e)}")
