class ConversationMessage {
  role "user" | "assistant"
  content string
}

function Router(message: string, conversation_history: ConversationMessage[]) -> string {
  client FastGemini
  prompt #"
    You are a verbose and helpful assistant. Provide comprehensive, detailed, and proactive answers.
    Explain your reasoning, break down complex topics, and anticipate user needs.
    Maintain a friendly tone and use the conversation history for context.

    CONVERSATION HISTORY:
    {% for msg in conversation_history -%}
    {{ msg.role | capitalize }}: {{ msg.content }}
    {% endfor %}

    Current Question: {{ message }}

    Your detailed and helpful response:
  "#
}

test TestRouter1{
    functions [Router]
    args {
        message "What is the capital of France?"
        conversation_history [
            {role: "user", content: "Hello"}
            {role: "assistant", content: "Hi"}
        ]
    }
}
