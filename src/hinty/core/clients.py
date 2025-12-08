import os
from loguru import logger
from baml_py import ClientRegistry


def get_client_registry(agent: str, multimodal: bool = False) -> ClientRegistry:
    logger.debug(
        f"Creating client registry for agent: {agent}, multimodal: {multimodal}"
    )
    """Create and return a ClientRegistry configured for the given agent.
    
    If multimodal is True, uses a model that supports multimodal input by checking
    the 'MULTIMODAL' environment variable.
    """
    env_key = "MULTIMODAL" if multimodal else f"{agent}".upper()
    model_str = os.environ.get(env_key)
    if not model_str:
        logger.error(
            f"Environment variable '{env_key}' not set for agent {agent} (multimodal={multimodal})"
        )
        raise ValueError(
            f"Environment variable '{env_key}' not set for agent {agent} (multimodal={multimodal})"
        )

    try:
        provider, model = model_str.split("/", 1)
    except ValueError:
        logger.error(
            f"Invalid model format in '{env_key}' for agent {agent} (multimodal={multimodal}): {model_str}"
        )
        raise ValueError(
            f"Invalid model format in '{env_key}' for agent {agent} (multimodal={multimodal}): {model_str}"
        )

    # Handle special providers that use openai-generic
    base_url = None
    if provider == "groq":
        actual_provider = "openai-generic"
        base_url = "https://api.groq.com/openai/v1"
        api_key_env = "GROQ_API_KEY"
    elif provider == "openrouter":
        actual_provider = "openai-generic"
        base_url = "https://openrouter.ai/api/v1"
        api_key_env = "OPENROUTER_API_KEY"
    elif provider.startswith("google"):
        actual_provider = "google-ai"
        api_key_env = "GOOGLE_API_KEY"
    else:
        logger.error(
            f"Unknown provider {provider} in '{env_key}' for agent {agent} (multimodal={multimodal})"
        )
        raise ValueError(
            f"Unknown provider {provider} in '{env_key}' for agent {agent} (multimodal={multimodal})"
        )

    api_key = os.environ.get(api_key_env)
    if not api_key:
        logger.error(
            f"API key for provider {provider} (from '{env_key}', agent {agent}, multimodal={multimodal}) not found in environment variables"
        )
        raise ValueError(
            f"API key for provider {provider} (from '{env_key}', agent {agent}, multimodal={multimodal}) not found in environment variables"
        )

    cr = ClientRegistry()
    client_name = f"{agent}_client"
    options = {
        "model": model,
        "api_key": api_key,
    }
    if base_url:
        options["base_url"] = base_url
    cr.add_llm_client(
        name=client_name,
        provider=actual_provider,
        options=options,
    )
    cr.set_primary(client_name)
    logger.debug(
        f"Client registry created successfully for agent: {agent}, multimodal: {multimodal}"
    )
    return cr
