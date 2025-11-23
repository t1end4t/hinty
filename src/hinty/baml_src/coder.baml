class CoderOutput {
  diff_content string
  response string
}

function Coder(
  user_message: string,
  file_content: string,
  file_path: string,
  conversation_history: ConversationMessage[]
) -> CoderOutput {
  client GroqRouter
  
  prompt #"
    You are an expert code editor assistant.
    
    Your task is to modify code based on the user's request and generate a unified diff.
    
    IMPORTANT RULES:
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
    
    Generate a unified diff (in standard diff -u format) that shows the changes needed to address the user's request.
    The diff should include the file path and be directly applicable by tools like patch.
    
    Also provide a clear response explaining the changes made and why.

    {{ ctx.output_format }}
  "#
}

test CoderSimpleChange {
  functions [Coder]
  args {
    user_message "Change the greeting to say 'Hi there!'"
    file_content #"
def hello():
    print("Hello, World!")
"#
    file_path "example.py"
    conversation_history []
  }
}
