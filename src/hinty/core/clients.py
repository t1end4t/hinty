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
    
    # Determine API key environment variable based on provider
    if provider == "groq":
        api_key_env = "GROQ_API_KEY"
    elif provider.startswith("google"):
        api_key_env = "GOOGLE_API_KEY"
    elif provider == "openrouter":
        api_key_env = "OPENROUTER_API_KEY"
    else:
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
