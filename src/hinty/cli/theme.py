from prompt_toolkit.styles import Style

# Catppuccin Mocha color palette constants
BLUE = "#89b4fa"
YELLOW = "#f9e2af"
GREEN = "#a6e3a1"
BASE = "#1e1e2e"
TEXT = "#cdd6f4"
SURFACE0 = "#313244"
SURFACE1 = "#45475a"
SURFACE2 = "#585b70"
SUBTEXT0 = "#a6adc8"
SUBTEXT1 = "#bac2de"
OVERLAY0 = "#6c7086"
OVERLAY1 = "#7f849c"
OVERLAY2 = "#9399b2"

# Catppuccin Mocha theme for prompt_toolkit
# NOTE: get from https://github.com/prompt-toolkit/python-prompt-toolkit/blob/main/src/prompt_toolkit/styles/defaults.py
catppuccin_mocha_style = Style.from_dict(
    {
        "prompt": f"bold {BLUE}",
        "completion-menu": f"bg:{BASE} {TEXT}",
        "completion-menu.completion": f"bg:{SURFACE0} {TEXT}",
        "completion-menu.completion.current": f"bg:{SURFACE1} {TEXT} bold",
        # Fuzzy matches in completion menu (for FuzzyCompleter).
        "completion-menu.completion fuzzymatch.outside": f"fg:{SUBTEXT0}",
        "completion-menu.completion fuzzymatch.inside": "bold",
        "completion-menu.completion fuzzymatch.inside.character": f"underline {OVERLAY2}",
        "completion-menu.completion.current fuzzymatch.outside": f"fg:{TEXT}",
        "completion-menu.completion.current fuzzymatch.inside": "nobold",
    }
)

# Rich Panel border style for Catppuccin Mocha theme
context_style = GREEN
agent_response_style = BLUE
agent_action_style = YELLOW
agent_thinking_style = SUBTEXT1
