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
You are an expert code editor assistant. Analyze the provided files and generate precise search/replace blocks to implement the requested changes.

FILES TO MODIFY:
{% for file in files %}
{{ file.file_path }}
```
{{ file.file_content }}
```

{% endfor %}

{% if conversation_history|length > 0 %}
PREVIOUS CONVERSATION:
{% for msg in conversation_history %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}

{% endif %}

USER REQUEST:
{{ user_message }}

OUTPUT FORMAT:
Generate search/replace blocks using this exact format:

file_path
```language
<<<<<<< SEARCH
[exact code to find - must match precisely including whitespace]
=======
[replacement code with same indentation]
>>>>>>> REPLACE
```

CRITICAL REQUIREMENTS:
1. SEARCH blocks must match original code exactly (whitespace, indentation, everything)
2. Make only minimal changes needed to address the request
3. Preserve existing code style and formatting conventions
4. Create separate blocks for each distinct change location
5. After all blocks, explain what changed and why

{{ ctx.output_format }}
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
