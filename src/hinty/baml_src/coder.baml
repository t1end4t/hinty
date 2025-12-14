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
  thinking string @description("Your thought process - explain what you're doing and why, like talking to a colleague")
  files_to_change FileChange[] @description("List of files with their respective changes")
  additional_files_to_check string[] @description("Other files that might need updating based on these changes")
  summary string @description("Final wrap-up of what changed and why it solves the problem")
}

class FileInfo {
  file_path string
  file_content string
}

class RelatedFile {
  file_path string
  relationship string @description("How it relates: imports_from, imported_by, uses, used_by, tests")
  relevant_excerpt string @description("Key functions/classes that matter")
}

class CodebaseContext {
  file_tree string @description("Tree structure of the project")
  related_files RelatedFile[] @description("Files connected to the ones being edited")
  project_language string @description("Primary language: python, javascript, typescript, etc.")
}

function Coder(
  user_message: string,
  conversation_history: ConversationMessage[],
  files: FileInfo[],
  codebase_context: CodebaseContext?,
) -> CoderOutput {
  client GroqRouter
  prompt #"
You are an expert developer working on a codebase. Think and communicate like a human coder who understands the full context of the project.

{% if codebase_context %}
PROJECT OVERVIEW:
{% if codebase_context.project_language %}
Language: {{ codebase_context.project_language }}
{% endif %}

PROJECT STRUCTURE:
{{ codebase_context.file_tree }}

{% if codebase_context.related_files|length > 0 %}
RELATED FILES (dependencies and connections):
{% for related in codebase_context.related_files %}
{{ related.file_path }} ({{ related.relationship }})
{{ related.relevant_excerpt }}

{% endfor %}
{% endif %}
{% endif %}

FILES I'M WORKING WITH:
{% for file in files %}
```
{{ file.file_content }}
```

{% endfor %}

{% if conversation_history|length > 0 %}
CONTEXT FROM OUR CONVERSATION:
{% for msg in conversation_history %}
{{ msg.role }}: {{ msg.content }}
{% endfor %}

{% endif %}
WHAT YOU NEED TO DO:
{{ user_message }}

HOW TO APPROACH THIS:

1. THINKING SECTION - Reason through the problem like a developer would:
   - Start with: "Ok, looking at this request..."
{% if codebase_context %}
   - Consider the project structure: "I can see this is a {{ codebase_context.project_language if codebase_context }} project..." 
{% endif %}
   - Identify what needs changing: "I need to modify [file] because..."
   - Think about related files: "This might affect [other files] since..."
   - Plan your approach: "The best way to handle this is..."
   
   Be conversational and thorough. Show your reasoning process.

2. MAKE YOUR CHANGES - For each file you identified:
   - Create precise search/replace blocks
   - CRITICAL: Search text must be EXACT matches from the original file (including all whitespace)
   - Maintain the same indentation style (match spaces/tabs exactly)
   - Make surgical, targeted changes - only touch what needs changing
   - If you need to change multiple locations in a file, create separate blocks for each
   - In the explanation field, describe what you changed and why

3. FLAG RELATED FILES - Think about ripple effects:
   - If you changed a function signature, what calls it?
   - If you modified an import, what else imports from there?
   - Are there tests that need updating?
   - List these in additional_files_to_check

4. SUMMARY - Wrap up naturally:
   - "So to recap, I've..."
   - List the key changes you made
   - Explain why this solves the problem
   - Mention any follow-up work needed

TECHNICAL RULES FOR SEARCH/REPLACE:
- Search blocks must match exactly (every space, tab, newline)
- Each search block should be unique within its file
- Preserve the existing code style and formatting
- Don't search for partial lines - include full lines with proper indentation
- If a line has leading spaces/tabs, include them in the search block

CONTEXT AWARENESS:
- Use the file tree to understand project organization
- Check related files to avoid breaking dependencies
- Match the project's language conventions and framework patterns
- Consider imports and how files connect to each other

Think of this like pair programming with someone who trusts your judgment. Be helpful, clear, and consider the broader impact of your changes.

{{ ctx.output_format }}
  "#
}


// Test 1: Simple bug fix in a single file
test TestSimpleBugFix {
  functions [Coder]
  args {
    user_message "Fix the typo in the greeting message - it should say 'Hello' not 'Helo'"
    files [
      {
        file_path "src/greeter.py"
        file_content #"
def greet(name):
    return f"Helo, {name}!"

def main():
    print(greet("World"))
"#
      }
    ]
    codebase_context null
    conversation_history []
  }
}

// Test 2: Multi-file refactoring with context
test TestRefactorWithContext {
  functions [Coder]
  args {
    user_message "Rename the 'calculate_total' function to 'compute_sum' across all files"
    files [
      {
        file_path "src/calculator.py"
        file_content #"
def calculate_total(numbers):
    return sum(numbers)

def get_average(numbers):
    total = calculate_total(numbers)
    return total / len(numbers)
"#
      },
      {
        file_path "src/main.py"
        file_content #"
from calculator import calculate_total

def process_data(data):
    result = calculate_total(data)
    print(f"Total: {result}")
"#
      }
    ]
    codebase_context {
      file_tree #"
src/
├── calculator.py
├── main.py
└── test_calculator.py
"#
      related_files [
        {
          file_path "src/test_calculator.py"
          relationship "tests"
          relevant_excerpt #"
def test_calculate_total():
    assert calculate_total([1, 2, 3]) == 6
"#
        }
      ]
      project_language "python"
      project_framework null
    }
    conversation_history []
  }
}

// Test 3: Adding new functionality with framework context
test TestAddReactComponent {
  functions [Coder]
  args {
    user_message "Add a loading state to the UserProfile component that shows a spinner while data is being fetched"
    files [
      {
        file_path "src/components/UserProfile.jsx"
        file_content #"
import React from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => setUser(data));
  }, [userId]);

  return (
    <div className="profile">
      <h2>{user?.name}</h2>
      <p>{user?.email}</p>
    </div>
  );
}

export default UserProfile;
"#
      }
    ]
    codebase_context {
      file_tree #"
src/
├── components/
│   ├── UserProfile.jsx
│   └── Spinner.jsx
├── utils/
│   └── api.js
└── App.jsx
"#
      related_files [
        {
          file_path "src/components/Spinner.jsx"
          relationship "used_by"
          relevant_excerpt #"
export function Spinner() {
  return <div className="spinner">Loading...</div>;
}
"#
        }
      ]
      project_language "javascript"
      project_framework "React"
    }
    conversation_history []
  }
}

// Test 4: Multiple changes in same file
test TestMultipleChangesInFile {
  functions [Coder]
  args {
    user_message "Update all print statements to use logging instead, and add proper error handling"
    files [
      {
        file_path "src/processor.py"
        file_content #"
def process_file(filepath):
    print(f"Processing {filepath}")
    
    with open(filepath, 'r') as f:
        data = f.read()
    
    print("File read successfully")
    
    result = transform(data)
    print(f"Transformation complete: {len(result)} bytes")
    
    return result

def transform(data):
    return data.upper()
"#
      }
    ]
    codebase_context {
      file_tree #"
src/
├── processor.py
└── config.py
"#
      related_files []
      project_language "python"
      project_framework null
    }
    conversation_history []
  }
}

// Test 5: With conversation history
test TestWithConversationContext {
  functions [Coder]
  args {
    user_message "Now also update the email validation to check for the domain"
    files [
      {
        file_path "src/validators.py"
        file_content #"
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    return len(phone) >= 10
"#
      }
    ]
    codebase_context null
    conversation_history [
      {
        role "user"
        content "Can you improve the email validation function?"
      },
      {
        role "assistant"
        content "I've added regex pattern validation to check email format properly."
      }
    ]
  }
}

// Test 6: Complex indentation preservation
test TestIndentationPreservation {
  functions [Coder]
  args {
    user_message "Add a check to ensure the user is authenticated before processing"
    files [
      {
        file_path "src/api/routes.js"
        file_content #"
const express = require('express');
const router = express.Router();

router.post('/submit', async (req, res) => {
    try {
        const data = req.body;
        const result = await processData(data);
        res.json({ success: true, result });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
"#
      }
    ]
    codebase_context {
      file_tree #"
src/
├── api/
│   ├── routes.js
│   └── middleware.js
└── utils/
    └── auth.js
"#
      related_files [
        {
          file_path "src/api/middleware.js"
          relationship "uses"
          relevant_excerpt #"
function requireAuth(req, res, next) {
  if (!req.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
}
"#
        }
      ]
      project_language "javascript"
      project_framework "Express"
    }
    conversation_history []
  }
}

// Test 7: Edge case - empty file or minimal change
test TestMinimalChange {
  functions [Coder]
  args {
    user_message "Change the constant value from 100 to 200"
    files [
      {
        file_path "src/config.py"
        file_content #"
MAX_RETRIES = 100
TIMEOUT = 30
"#
      }
    ]
    codebase_context null
    conversation_history []
  }
}

// Test 8: Type system changes affecting multiple files
test TestTypeSystemChange {
  functions [Coder]
  args {
    user_message "Change the User interface to make email optional and add a phone number field"
    files [
      {
        file_path "src/types/user.ts"
        file_content #"
export interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

export interface UserCreateRequest {
  name: string;
  email: string;
}
"#
      }
    ]
    codebase_context {
      file_tree #"
src/
├── types/
│   └── user.ts
├── services/
│   └── userService.ts
└── components/
    └── UserForm.tsx
"#
      related_files [
        {
          file_path "src/services/userService.ts"
          relationship "uses"
          relevant_excerpt #"
import { User, UserCreateRequest } from '../types/user';

export function createUser(data: UserCreateRequest): User {
  // implementation
}
"#
        },
        {
          file_path "src/components/UserForm.tsx"
          relationship "uses"
          relevant_excerpt #"
import { UserCreateRequest } from '../types/user';

function UserForm() {
  const [email, setEmail] = useState('');
  // ...
}
"#
        }
      ]
      project_language "typescript"
      project_framework "React"
    }
    conversation_history []
  }
}
