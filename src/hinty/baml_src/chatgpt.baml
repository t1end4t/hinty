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
  tool_call (SearchWebTool | FetchUrlTool)? @description("The tool to use if additional information is needed, or null if you can answer directly")
  requires_tool bool @description("True if a tool is needed to provide a complete answer, false if the response is complete")
}

// Single function that returns response and determines tool usage with multimodal support
function ChatGPT(
  message: string,
  conversation_history: ConversationMessage[]?,
  additional_files: map<string, string>[]?,
  additional_images: image[]?,
  additional_docs: pdf[]?,
  tool_result: ToolResult?
) -> ChatGPTOutput {
  client GroqRouter
  prompt #"
You are a helpful AI assistant that can use tools when needed and process multimodal inputs including text files, images, and PDFs.

Your goal is to provide accurate, helpful responses by:
1. Using your knowledge when sufficient
2. Calling tools when additional information is needed
3. Processing and synthesizing information from all provided sources

Available tools:
- search_web: Search the internet for current information
- fetch_url: Retrieve content from a specific URL

Important rules for interaction:
- Process all provided multimodal inputs (text files, images, PDFs) to understand full context
- For images: Analyze visual content, extract text if present, identify relevant information
- For PDFs: Read and extract relevant information from documents
- For text files: Use provided file content to inform your response
- If you can answer directly with your knowledge or provided content, set requires_tool to false
- If you need additional information (web search or URL fetch), set requires_tool to true and specify tool_call
- Always provide a response even if a tool is needed
- Synthesize information from all sources for comprehensive answers

{% if conversation_history %}
Here is the conversation history prior to the current question:
{% for msg in conversation_history -%}
{{ msg.role | capitalize }}: {{ msg.content }}
{% endfor %}

{% endif %}
{% if additional_files %}
Here are the text files provided:
{% for file in additional_files %}
{{ file }}

{% endfor %}
{% endif %}
{% if additional_images %}
Here are the images provided:
{% for image in additional_images %}
{{ image }}
{% endfor %}

{% endif %}
{% if additional_docs %}
Here are the PDF documents provided:
{% for pdf in additional_docs %}
{{ pdf }}
{% endfor %}

{% endif %}
{% if tool_result %}
Here is the result from the tool you called:
Tool: {{ tool_result.name }}
{% if tool_result.success %}
Result: {{ tool_result.output }}
{% else %}
Error: {{ tool_result.error }}
{% endif %}

Use this tool result along with any provided content to answer the question.

{% endif %}
Here is the user's current question:
{{ message }}

Think about your answer first. Consider:
1. Can I answer this with available information, or do I need to call a tool?
2. What information from the provided sources (history, files, images, PDFs, tools) is relevant?
3. How can I synthesize all relevant information into a helpful response?

Now provide your response following the specified output format.
{{ ctx.output_format }}
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
        additional_files [
            {"file1.txt": "Your name is Dat."},
            {"file2.txt": "Your name is Dat."}
        ]
    }
}

test TestChatgpt2{
    functions [ChatGPT]
    args {
        message "What is the capital of France?"
    }
}
