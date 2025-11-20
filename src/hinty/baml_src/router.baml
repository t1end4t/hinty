class ConversationMessage {
  role "user" | "assistant"
  content string
}

function Router(message: string, conversation_history: ConversationMessage[]?) -> string {
  client GroqRouter
  prompt #"
    You are a helpful assistant.

    {% if conversation_history %}
    CONVERSATION HISTORY:
    {% for msg in conversation_history -%}
    {{ msg.role | capitalize }}: {{ msg.content }}
    {% endfor %}
    {% endif %}

    Current Question: {{ message }}

    Your helpful response:
  "#
}

test TestRouter1{
    functions [Router]
    args {
        message "Do you remember my name?"
        conversation_history [
            {role: "user", content: "Hi, I am Dat"}
            {role: "assistant", content: "Hi Dat"}
        ]
    }
}

test TestRouter2{
    functions [Router]
    args {
        message "What is the capital of France?"
    }
}
