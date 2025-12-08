import os
from loguru import logger
from baml_py import ClientRegistry


def get_model_str(agent: str, multimodal: bool) -> str:
    env_key = "MULTIMODAL" if multimodal else f"{agent}".upper()
    model_str = os.environ.get(env_key)
    if not model_str:
        logger.error(
            f"Environment variable '{env_key}' not set for agent {agent} (multimodal={multimodal})"
        )
        raise ValueError(
            f"Environment variable '{env_key}' not set for agent {agent} (multimodal={multimodal})"
        )
    return model_str


def parse_provider_model(
    model_str: str, env_key: str, agent: str, multimodal: bool
) -> tuple[str, str]:
    try:
        provider, model = model_str.split("/", 1)
    except ValueError:
        logger.error(
            f"Invalid model format in '{env_key}' for agent {agent} (multimodal={multimodal}): {model_str}"
        )
        raise ValueError(
            f"Invalid model format in '{env_key}' for agent {agent} (multimodal={multimodal}): {model_str}"
        )
    return provider, model


def get_provider_config(provider: str) -> tuple[str, str | None, str]:
    if provider == "groq":
        return (
            "openai-generic",
            "https://api.groq.com/openai/v1",
            "GROQ_API_KEY",
        )
    elif provider == "openrouter":
        return (
            "openai-generic",
            "https://openrouter.ai/api/v1",
            "OPENROUTER_API_KEY",
        )
    elif provider.startswith("google"):
        return "google-ai", None, "GOOGLE_API_KEY"
    else:
        raise ValueError(f"Unknown provider {provider}")


def get_api_key(
    api_key_env: str, provider: str, env_key: str, agent: str, multimodal: bool
) -> str:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        logger.error(
            f"API key for provider {provider} (from '{env_key}', agent {agent}, multimodal={multimodal}) not found in environment variables"
        )
        raise ValueError(
            f"API key for provider {provider} (from '{env_key}', agent {agent}, multimodal={multimodal}) not found in environment variables"
        )
    return api_key


def get_client_registry(agent: str, multimodal: bool = False) -> ClientRegistry:
    """Create and return a ClientRegistry configured for the given agent.

    If multimodal is True, uses a model that supports multimodal input by checking
    the 'MULTIMODAL' environment variable.
    """
    logger.debug(
        f"Creating client registry for agent: {agent}, multimodal: {multimodal}"
    )
    env_key = "MULTIMODAL" if multimodal else f"{agent}".upper()
    model_str = get_model_str(agent, multimodal)
    provider, model = parse_provider_model(
        model_str, env_key, agent, multimodal
    )
    actual_provider, base_url, api_key_env = get_provider_config(provider)
    api_key = get_api_key(api_key_env, provider, env_key, agent, multimodal)
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
