import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logger = logging.getLogger(__name__)

def get_llm(google_api_key: str = None, model_name: str = None, temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    """
    Initializes and returns the ChatGoogleGenerativeAI LLM object.
    It automatically queries the Google API to discover supported chat models
    and maps the user's choice to the correct API model name.
    
    Args:
        google_api_key (str): Optional Google API key passed from UI.
        model_name (str): Optional Google model name (e.g., 'gemini-1.5-flash').
        temperature (float): Controls response randomness/creativity. Default is 0.0.
        
    Returns:
        ChatGoogleGenerativeAI: The resolved ChatGoogleGenerativeAI model object.
    """
    logger.info("Initializing Google Gemini Chat LLM model")
    
    # Resolve API Key
    api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("No Google Gemini API key provided. Cannot initialize LLM.")
        raise ValueError(
            "Google Gemini API Key is missing. Please set it in your environment or provide it in the UI."
        )
        
    # Standard fallback name
    resolved_model_name = model_name or os.getenv("MODEL_NAME", "gemini-1.5-flash")
    
    # Auto-detect supported generation models via official google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        discovered_gen_models = []
        for m in client.models.list():
            # Check if this model supports generateContent method
            if m.supported_actions and any("generatecontent" in action.lower() for action in m.supported_actions):
                discovered_gen_models.append(m.name)
                
        if discovered_gen_models:
            logger.info(f"Discovered generation models from Gemini API: {discovered_gen_models}")
            
            # Look for exact matching name (with or without 'models/' prefix)
            match_found = False
            for dm in discovered_gen_models:
                dm_clean = dm.replace("models/", "")
                rm_clean = resolved_model_name.replace("models/", "")
                if dm_clean == rm_clean:
                    logger.info(f"Matched model {resolved_model_name} to discovered API name: {dm}")
                    resolved_model_name = dm
                    match_found = True
                    break
            
            # Fuzzy match if exact match not found
            if not match_found:
                for dm in discovered_gen_models:
                    if resolved_model_name in dm or dm in resolved_model_name:
                        logger.info(f"Fuzzy matched model {resolved_model_name} to: {dm}")
                        resolved_model_name = dm
                        match_found = True
                        break
            
            # Fallback to first available flash model if no match found
            if not match_found:
                flash_models = [m for m in discovered_gen_models if "flash" in m.lower()]
                if flash_models:
                    resolved_model_name = flash_models[0]
                else:
                    resolved_model_name = discovered_gen_models[0]
                logger.warning(
                    f"Selected model '{model_name}' was not found in available list. "
                    f"Auto-selected fallback: {resolved_model_name}"
                )
    except Exception as e:
        logger.warning(f"Could not discover generation models list from Google API: {e}. Using default model name.")
        
    logger.info(f"Initializing ChatGoogleGenerativeAI with resolved model name: {resolved_model_name}")
    
    try:
        llm = ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=resolved_model_name,
            temperature=temperature,
            max_retries=2
        )
        logger.info("Successfully initialized ChatGoogleGenerativeAI model.")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to initialize LLM: {str(e)}")
