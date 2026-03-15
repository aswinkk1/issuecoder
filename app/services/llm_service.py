import os
import logging
from langchain_openai import ChatOpenAI
# You can add other providers like Anthropic or a local LLM (e.g., via Ollama/Llama.cpp)

logger = logging.getLogger(__name__)

class LLMFactory:
    @staticmethod
    def get_llm():
        """
        Returns a configured LangChain ChatModel based on environment variables.
        Supports 'openai' or 'local'.
        """
        provider = os.environ.get("LLM_PROVIDER", "openai").lower()
        
        if provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY is not set.")
                return None
            logger.info("Initializing OpenAI LLM.")
            return ChatOpenAI(temperature=0, model_name="gpt-4")
            
        elif provider == "local":
            # Example: Connect to a local OpenAI-compatible API (like LM Studio or Ollama)
            base_url = os.environ.get("LOCAL_LLM_URL", "http://localhost:11434/v1")
            api_key = os.environ.get("LOCAL_LLM_KEY", "not-needed")
            model = os.environ.get("LOCAL_LLM_MODEL", "llama2")
            logger.info(f"Initializing Local LLM at {base_url} with model {model}.")
            return ChatOpenAI(
                temperature=0, 
                openai_api_key=api_key, 
                openai_api_base=base_url,
                model_name=model
            )
            
        else:
            logger.error(f"Unsupported LLM provider: {provider}")
            return None
