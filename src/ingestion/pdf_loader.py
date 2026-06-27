import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader

# Configure logging
logger = logging.getLogger(__name__)

def load_pdf(file_path: str) -> List[Document]:
    """
    Loads and parses a PDF document using PyPDFLoader.
    
    Args:
        file_path (str): Path to the PDF file.
        
    Returns:
        List[Document]: List of LangChain Document objects containing page content and metadata.
    """
    logger.info(f"Starting PDF ingestion for file: {file_path}")
    try:
        # Load and split using PyPDFLoader
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        logger.info(f"Successfully loaded PDF. Extracted {len(documents)} pages.")
        return documents
    except Exception as e:
        logger.error(f"Failed to load PDF file {file_path}: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error parsing PDF file: {str(e)}")
