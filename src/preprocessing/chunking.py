import logging
from typing import List
from langchain_core.documents import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logger = logging.getLogger(__name__)

def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Splits documents into smaller chunks using RecursiveCharacterTextSplitter.
    
    Args:
        documents (List[Document]): The list of ingested LangChain documents.
        chunk_size (int): The target size of each text chunk in characters.
        chunk_overlap (int): The number of overlapping characters between adjacent chunks.
        
    Returns:
        List[Document]: List of split document chunks.
    """
    logger.info(f"Chunking {len(documents)} documents (size={chunk_size}, overlap={chunk_overlap})")
    
    # Input validation
    if chunk_size <= 0:
        logger.error(f"Invalid chunk_size: {chunk_size}. Must be greater than 0.")
        raise ValueError("Chunk size must be a positive integer.")
    if chunk_overlap < 0:
        logger.error(f"Invalid chunk_overlap: {chunk_overlap}. Must be non-negative.")
        raise ValueError("Chunk overlap must be a non-negative integer.")
    if chunk_overlap >= chunk_size:
        logger.error(f"Chunk overlap ({chunk_overlap}) cannot be greater than or equal to chunk size ({chunk_size}).")
        raise ValueError("Chunk overlap must be less than chunk size.")
        
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            add_start_index=True
        )
        
        chunks = splitter.split_documents(documents)
        logger.info(f"Successfully chunked documents. Created {len(chunks)} chunks.")
        return chunks
    except Exception as e:
        logger.error(f"Error during document chunking: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error splitting documents: {str(e)}")
