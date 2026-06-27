import logging
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader

# Configure logging
logger = logging.getLogger(__name__)

def load_txt(file_path: str) -> List[Document]:
    """
    Loads and parses a TXT document using TextLoader.
    
    Args:
        file_path (str): Path to the TXT file.
        
    Returns:
        List[Document]: List of LangChain Document objects containing text content.
    """
    logger.info(f"Starting TXT ingestion for file: {file_path}")
    try:
        # Load using TextLoader with UTF-8 encoding
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
        logger.info(f"Successfully loaded TXT file. Extracted {len(documents)} document sections.")
        return documents
    except Exception as e:
        logger.error(f"Failed to load TXT file {file_path}: {str(e)}", exc_info=True)
        raise RuntimeError(f"Error parsing TXT file: {str(e)}")
