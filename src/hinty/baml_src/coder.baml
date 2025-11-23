class CoderOutput {
  diff_content string
  response string
}
  
class FileInfo {
  file_path string
  file_content string
}
  
function Coder(
  user_message: string,
  files: FileInfo[],
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
    
    {% for file in files %}
    FILE: {{ file.file_path }}
    
    ORIGINAL CONTENT:
    ```
    {{ file.file_content }}
    ```

    {% endfor %}

    {% if conversation_history|length > 0 %}
    CONVERSATION HISTORY:
    {% for msg in conversation_history %}
    {{ msg.role }}: {{ msg.content }}
    {% endfor %}
    {% endif %}
      
    USER REQUEST:
    {{ user_message }}

    Generate search/replace blocks that show the changes needed to address the user's request.
    Use the following format for each block:

    file_path
    ```language
    <<<<<<< SEARCH
    old_content
  "#
}
  
test CoderSimpleChange {
  functions [Coder]
  args {
    user_message "Change the greeting to say 'Hi there!'"
    files [
      {
        file_path "example.py"
        file_content #"
def hello():
    print("Hello, World!")
"#
      }
    ]
    conversation_history []
  }
}
