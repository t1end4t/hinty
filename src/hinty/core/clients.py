import os
from baml_py import ClientRegistry


def get_client_registry(agent: str) -> ClientRegistry:
    """Create and return a ClientRegistry configured for the given agent."""
    model_str = os.environ.get(f"{agent.upper()}_MODEL")
    if not model_str:
        raise ValueError(
            f"Model for {agent} not found in environment variables"
        )

    try:
        provider, model = model_str.split("/", 1)
    except ValueError:
        raise ValueError(f"Invalid model format for {agent}: {model_str}")

    api_key_env_map = {
        "groq": "GROQ_API_KEY",
        "google": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    api_key_env = api_key_env_map.get(provider)
    if not api_key_env:
        raise ValueError(f"Unknown provider {provider} for agent {agent}")

    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(
            f"API key for provider {provider} not found in environment variables"
        )

    cr = ClientRegistry()
    client_name = f"{agent}_client"
    cr.add_llm_client(
        name=client_name,
        provider=provider,
        options={
            "model": model,
            "api_key": api_key,
        },
    )
    cr.set_primary(client_name)
    return cr
