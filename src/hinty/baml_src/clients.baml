// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview
client<llm> GeminiGeneral {
  provider google-ai
  retry_policy Exponential
  options {
    model "gemini-flash-latest"
  }
}

client<llm> GroqRouter {
  provider openai-generic
  retry_policy Exponential
  options {
    base_url "https://api.groq.com/openai/v1"
    api_key env.GROQ_API_KEY
    model "openai/gpt-oss-120b"
  }
}


client<llm> GrokCoder {
  provider "openai-generic"
  retry_policy Exponential
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "x-ai/grok-code-fast-1"
  }
}

client<llm> ClaudeWriter {
  provider "openai-generic"
  retry_policy Exponential
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "anthropic/claude-sonnet-4.5"
  }
}

client<llm> Thinking {
  provider "openai-generic"
  retry_policy Exponential
  options {
    base_url "https://openrouter.ai/api/v1"
    api_key env.OPENROUTER_API_KEY
    model "anthropic/claude-opus-4.1"
  }
}

// https://docs.boundaryml.com/docs/snippets/clients/retry
retry_policy Constant {
  max_retries 3
  strategy {
    type constant_delay
    delay_ms 200
  }
}

retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}