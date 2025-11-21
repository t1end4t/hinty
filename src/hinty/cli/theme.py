from prompt_toolkit.styles import Style

# Catppuccin Mocha color palette constants
BLUE = "#89b4fa"
BASE = "#1e1e2e"
TEXT = "#cdd6f4"
SURFACE0 = "#313244"
YELLOW = "#f9e2af"
SUBTEXT0 = "#a6adc8"
SURFACE1 = "#45475a"
SUBTEXT1 = "#bac2de"
GREEN = "#a6e3a1"
PINK = "#f5c2e7"

# Catppuccin Mocha theme for prompt_toolkit
catppuccin_mocha_style = Style.from_dict(
    {
        "prompt": f"bold {BLUE}",
        "completion-menu": f"bg:{BASE} {TEXT}",
        "completion-menu.completion": f"bg:{SURFACE0} {TEXT}",
        "completion-menu.completion.current": f"bg:{SURFACE1} {TEXT} bold",
        # Fuzzy matches in completion menu (for FuzzyCompleter).
        "completion-menu.completion fuzzymatch.outside": f"fg:{SUBTEXT0}",
        "completion-menu.completion fuzzymatch.inside": "bold",
        "completion-menu.completion fuzzymatch.inside.character": f"underline {PINK}",
        "completion-menu.completion.current fuzzymatch.outside": f"fg:{TEXT}",
        "completion-menu.completion.current fuzzymatch.inside": "nobold",
    }
)

# Rich Panel border style for Catppuccin Mocha theme
panel_border_style = BLUE  # Catppuccin Mocha Blue

# Files panel border style for Catppuccin Mocha theme
files_panel_border_style = GREEN  # Catppuccin Mocha Green
