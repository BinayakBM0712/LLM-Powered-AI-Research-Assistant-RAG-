import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import Docx2txtLoader

# Configure logging
logger = logging.getLogger(__name__)

def load_docx(file_path: str) -> List[Document]:
    """
    Loads and parses a DOCX document using Docx2txtLoader.
    
    Args:
        file_path (str): Path to the DOCX file.
        
    Returns:
        List[Document]: List of LangChain Document objects containing text content.
    """
    logger.info(f"Starting DOCX ingestion for file: {file_path}")
    try:
        # Load using Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        logger.info(f"Successfully loaded DOCX. Extracted {len(documents)} document sections.")
        return documents
    except Exception as e:
        logger.error(f"Failed to load DOCX file {file_path}: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error parsing DOCX file: {str(e)}")
