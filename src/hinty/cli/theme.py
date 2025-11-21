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

# Catppuccin Mocha theme for prompt_toolkit
catppuccin_mocha_style = Style.from_dict(
    {
        "prompt": f"bold {BLUE}",  # Catppuccin Mocha Blue
        # Completion menu styles for Catppuccin Mocha theme
        "completion-menu": f"bg:{BASE} {TEXT}",  # Base bg, Text fg
        "completion-menu.completion": f"bg:{SURFACE0} {TEXT}",  # Surface0 bg, Text fg
        "completion-menu.completion.current": f"bg:{SURFACE1} {YELLOW} bold",  # Surface1 bg, Yellow fg, bold
        "completion-menu.meta": f"bg:{BASE} {SUBTEXT0}",  # Base bg, Subtext0 fg
        "completion-menu.meta.current": f"bg:{SURFACE1} {SUBTEXT1} bold",  # Surface1 bg, Subtext1 fg, bold
    }
)

# Rich Panel border style for Catppuccin Mocha theme
panel_border_style = BLUE  # Catppuccin Mocha Blue

# Files panel border style for Catppuccin Mocha theme
files_panel_border_style = GREEN  # Catppuccin Mocha Green
