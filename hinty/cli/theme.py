from prompt_toolkit.styles import Style
from pydantic import BaseModel


class BaseTheme(BaseModel):
    """Base theme class."""

    blue: str = "#0000FF"
    green: str = "#008000"
    yellow: str = "#FFFF00"
    red: str = "#FF0000"
    overlay0: str = "#808080"
    surface0: str = "#D3D3D3"
    surface1: str = "#A9A9A9"
    text: str = "#000000"


class CatppuccinMochaTheme(BaseTheme):
    """Catppuccin Mocha theme colors."""

    blue: str = "#89b4fa"
    green: str = "#a6e3a1"
    yellow: str = "#f9e2af"
    red: str = "#f38ba8"
    overlay0: str = "#6c7086"
    surface0: str = "#313244"
    surface1: str = "#45475a"
    text: str = "#cdd6f4"


def create_catppuccin_theme() -> BaseTheme:
    """Create theme instance."""
    return CatppuccinMochaTheme()


def create_style(theme: BaseTheme) -> Style:
    """Create prompt toolkit style from theme."""
    return Style.from_dict(
        {
            "completion-menu": f"{theme.overlay0} bg:{theme.surface0}",
            "completion-menu.completion.current": f"{theme.text} bg:{theme.surface1}",
        }
    )
