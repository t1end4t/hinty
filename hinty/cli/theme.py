from prompt_toolkit.styles import Style

# Catppuccin Mocha theme for prompt_toolkit
catppuccin_mocha_style = Style.from_dict(
    {
        "prompt": "bold #89b4fa",  # Catppuccin Mocha Blue
        # Completion menu styles for Catppuccin Mocha theme
        "completion-menu": "bg:#1e1e2e #cdd6f4",  # Base bg, Text fg
        "completion-menu.completion": "bg:#313244 #cdd6f4",  # Surface0 bg, Text fg
        "completion-menu.completion.current": "bg:#45475a #f9e2af bold",  # Surface1 bg, Yellow fg, bold
        "completion-menu.meta": "bg:#1e1e2e #a6adc8",  # Base bg, Subtext0 fg
        "completion-menu.meta.current": "bg:#45475a #bac2de bold",  # Surface1 bg, Subtext1 fg, bold
    }
)

# Rich Panel border style for Catppuccin Mocha theme
panel_border_style = "#89b4fa"  # Catppuccin Mocha Blue
