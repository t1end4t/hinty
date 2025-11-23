class FileDiff {
  file_path string
  original_content string
  modified_content string
  explanation string
}

function Coder(
  user_message: string,
  file_content: string,
  file_path: string,
  conversation_history: ConversationMessage[]
) -> FileDiff {
  client GrokCoder
  
  prompt #"
    You are an expert code editor assistant.
    
    Your task is to modify code based on the user's request and generate a diff.
    
    IMPORTANT RULES:
    - Follow the coding principles in CLAUDE.md (readability, simplicity, functional programming)
    - Make minimal, focused changes that address the user's request
    - Preserve existing code style and formatting
    - Do not add unnecessary changes
    - Provide clear explanation of what changed and why
    
    CURRENT FILE: {{ file_path }}
    
    ORIGINAL CONTENT:
    ```
    {{ file_content }}
    ```
    
    {% if conversation_history|length > 0 %}
    CONVERSATION HISTORY:
    {% for msg in conversation_history %}
    {{ msg.role }}: {{ msg.content }}
    {% endfor %}
    {% endif %}
    
    USER REQUEST:
    {{ user_message }}
    
    Generate the modified version of the file that addresses the user's request.
    Provide a clear explanation of the changes made.
  "#
}
