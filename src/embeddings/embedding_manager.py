import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Configure logging
logger = logging.getLogger(__name__)

def get_embedding_model(google_api_key: str = None) -> GoogleGenerativeAIEmbeddings:
    """
    Initializes, tests, and returns a verified GoogleGenerativeAIEmbeddings model.
    It automatically queries the Google API to discover supported embedding models
    and verifies them with a dummy request to prevent runtime 404 errors.
    
    Args:
        google_api_key (str): Optional Google API key passed from UI.
        
    Returns:
        GoogleGenerativeAIEmbeddings: The verified Google Generative AI Embeddings object.
    """
    logger.info("Initializing Google Generative AI Embeddings")
    
    # Resolve API Key
    api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("No Google Gemini API key provided.")
        raise ValueError(
            "Google Gemini API Key is missing. Please set it in your environment or provide it in the UI."
        )
        
    # List of candidate models to try
    candidate_models = [
        "models/text-embedding-004",
        "text-embedding-004",
        "models/embedding-001",
        "embedding-001"
    ]
    
    # Try to discover supported embedding models using the official google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        discovered_models = []
        for m in client.models.list():
            # Check if this model supports embedding content
            if m.supported_actions and any("embed" in action.lower() for action in m.supported_actions):
                discovered_models.append(m.name)
                
        if discovered_models:
            logger.info(f"Discovered embedding models from Gemini API: {discovered_models}")
            # Prioritize discovered models by prepending them
            for model_name in reversed(discovered_models):
                if model_name not in candidate_models:
                    candidate_models.insert(0, model_name)
    except Exception as e:
        logger.warning(f"Could not fetch available models list from Google API: {e}. Falling back to default list.")
        
    # Iterate and find the first working model
    last_error = None
    for model_name in candidate_models:
        try:
            logger.info(f"Testing GoogleGenerativeAIEmbeddings with model: {model_name}")
            embeddings = GoogleGenerativeAIEmbeddings(
                google_api_key=api_key,
                model=model_name
            )
            # Test embed a short dummy query to verify permissions and endpoint availability
            embeddings.embed_query("ping")
            logger.info(f"Successfully verified and loaded embedding model: {model_name}")
            return embeddings
        except Exception as e:
            logger.warning(f"Google embedding model {model_name} failed verification: {str(e)}")
            last_error = e
            
    # Raise error if all models failed
    logger.error("All Google embedding models failed verification check.")
    raise RuntimeError(
        f"Failed to initialize any valid Google embedding model. Last error: {str(last_error)}"
    )
