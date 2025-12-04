// Define the conversation message structure
class ConversationMessage {
  role "user" | "assistant"
  content string
}

// Define available tools
class SearchWebTool {
  tool_name "search_web"
  query string @description("The search query to look up on the web")
}

class FetchUrlTool {
  tool_name "fetch_url"
  url string @description("The URL to fetch content from")
}

// Response that includes both the answer and optional tool call
class ChatGPTOutput {
  response string @description("Your helpful response to the user. If a tool is needed, explain what you're doing. If not, provide the complete answer.")
  tool_call SearchWebTool | FetchUrlTool | null @description("The tool to use if additional information is needed, or null if you can answer directly")
  requires_tool bool @description("True if a tool is needed to provide a complete answer, false if the response is complete")
}

// Single function that returns response and determines tool usage
function ChatGPT(
  message: string,
  conversation_history: ConversationMessage[]?,
  tool_result: map<string, string>?
) -> ChatGPTOutput {
  client GroqRouter
  prompt #"
    You are a helpful assistant that can use tools when needed.
    
    Available tools:
    1. search_web - Search the internet for current information
    2. fetch_url - Retrieve content from a specific URL
    
    {{ ctx.output_format }}
    
{% if conversation_history %}
    CONVERSATION HISTORY:
{% for msg in conversation_history -%}
{{ msg.role | capitalize }}: {{ msg.content }}
{% endfor %}
{% endif %}

{% if tool_result %}
TOOL RESULT:
    {{ tool_result }}
    
    Use the above tool result along with any provided file content to answer the question.
{% endif %}
    Current Question: {{ message }}
    
    Instructions:
    - If you can answer the question directly with your knowledge or the provided file content, set requires_tool to false and provide a complete response
    - If you need additional information (web search, URL fetch, RAG, or file write), set requires_tool to true, explain what you need to do, and specify the tool_call
    - Always provide a response even if a tool is needed
  "#
}

// Function to generate final response after tool execution
test TestChatgpt1{
    functions [ChatGPT]
    args {
        message "Do you remember my name?"
        conversation_history [
            {role: "user", content: "Hi, I am Dat"}
            {role: "assistant", content: "Hi Dat"}
        ]
    }
}

test TestChatgpt2{
    functions [ChatGPT]
    args {
        message "What is the capital of France?"
    }
}
