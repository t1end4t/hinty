class SearchReplaceBlock {
  search string @description("Exact code to find - must match precisely including whitespace")
  replace string @description("Replacement code with same indentation")
  language string @description("Programming language for syntax highlighting")
}

class FileChange {
  file_path string @description("Path to the file that needs modification")
  blocks SearchReplaceBlock[] @description("List of search/replace blocks to apply to this file")
  explanation string @description("Brief explanation of changes made to this file")
}

class CoderOutput {
  files_to_change FileChange[] @description("List of files with their respective changes")
  summary string @description("Overall summary of all changes")
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

FILES PROVIDED:
{% for file in files %}
=== {{ file.file_path }} ===
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

INSTRUCTIONS:
1. Identify which files need to be modified to fulfill the user's request
2. For each file that needs changes, create search/replace blocks
3. SEARCH blocks MUST match the original code exactly (whitespace, indentation, everything)
4. REPLACE blocks should preserve the existing code style and formatting
5. Make only minimal, targeted changes - don't rewrite entire functions unless necessary
6. Group related changes to the same file together
7. Provide clear explanations for each file's changes

CRITICAL RULES:
- Search text must be an exact substring from the original file
- Maintain consistent indentation (spaces vs tabs, amount)
- Preserve surrounding code context
- Each search block should be unique within its file
- If multiple changes are needed in one file, create separate blocks for each location

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

test CoderSimpleChange2 {
  functions [Coder]
  args {
    user_message "Add a new function that to tell get content from a URL, and also change function hello to say 'Hi there!'"
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