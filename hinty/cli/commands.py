from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from .context_manager import (
    ProjectContext,
    print_message,
)
from .models import COMMANDS, CommandHandler, Mode
from .theme import BaseTheme


def _print_command_output(
    console: Console,
    theme: BaseTheme,
    content: str = "",
    title: str = "Command Output",
):
    """Print command output with consistent formatting."""
    # Use red color for error titles
    if title == "Error":
        console.rule(f"[red]{title}[/red]", style=theme.red)
        if content:
            print_message(console, theme, content, "red")
        console.rule(style=theme.red)
    else:
        console.rule(f"[yellow]{title}[/yellow]", style=theme.yellow)
        if content:
            print_message(console, theme, content, "yellow")
        console.rule(style=theme.yellow)


def handle_exit_command(
    console: Console, theme: BaseTheme, _: ProjectContext
) -> bool:
    """Handle exit command."""
    _print_command_output(console, theme, "Goodbye!", "Command Output")
    return True


def _show_directory_contents(console: Console, theme: BaseTheme) -> None:
    """Show contents of current directory."""
    try:
        current_dir = Path(".")
        files = [f for f in current_dir.iterdir() if not f.name.startswith(".")]
        if files:
            file_list = "\n".join(
                [f"  {f.name}{'/' if f.is_dir() else ''}" for f in files[:10]]
            )
            if len(files) > 10:
                file_list += f"\n  ... and {len(files) - 10} more items"
            print_message(
                console,
                theme,
                f"Files in current directory:\n{file_list}",
                "blue",
            )
        else:
            print_message(console, theme, "Current directory is empty", "blue")
    except PermissionError:
        print_message(console, theme, "Cannot access current directory", "red")


def handle_add_command(
    console: Console,
    theme: BaseTheme,
    project_manager: ProjectContext,
    user_input: str = "",
) -> bool:
    """Handle add command."""
    console.rule("[yellow]Command Output[/yellow]", style=theme.yellow)

    if not user_input or user_input.strip() == "/add":
        print_message(console, theme, "Usage: /add <file_path>", "red")
        _show_directory_contents(console, theme)
        console.rule(style=theme.yellow)

        return False

    # Extract file path from command
    parts = user_input.split(" ", 1)
    if len(parts) < 2:
        _print_command_output(
            console, theme, "Usage: /add <file_path>", "Error"
        )

        return False

    file_path = parts[1].strip()

    try:
        path = Path(file_path)
        if not path.exists():
            _print_command_output(
                console, theme, f"File not found: {file_path}", "Error"
            )

            return False

        if path.is_dir():
            _print_command_output(
                console, theme, f"Cannot add directory: {file_path}", "Error"
            )
            return False

        # Add file to context
        project_manager.add_file(path)
        console.rule(style=theme.yellow)

        return False

    except Exception as e:
        _print_command_output(
            console, theme, f"Error adding file: {str(e)}", "Error"
        )

        return False


def handle_help_command(
    console: Console, theme: BaseTheme, _: ProjectContext
) -> bool:
    """Handle help command."""
    # Build help text from COMMANDS list
    command_help_lines = []
    for cmd in COMMANDS:
        command_help_lines.append(
            f"[bold {theme.blue}]{cmd.name}[/bold {theme.blue}] - {cmd.description}"
        )

    help_text = (
        f"[bold {theme.green}]Available Commands:[/bold {theme.green}]\n\n"
        + "\n".join(command_help_lines)
    )

    console.print(
        Panel(
            help_text,
            title=f"[bold {theme.yellow}]Help[/bold {theme.yellow}]",
            border_style=theme.yellow,
        )
    )

    return False


def handle_init_command(
    console: Console,
    theme: BaseTheme,
    project_manager: ProjectContext,
) -> bool:
    """Handle init command to initialize project paths."""
    try:
        _print_command_output(
            console,
            theme,
            "Project initialized successfully!",
            "Command Output",
        )
        return False
    except Exception as e:
        _print_command_output(
            console, theme, f"Error initializing project: {str(e)}", "Error"
        )
        return False


def handle_mode_command(
    user_input: str, console: Console, theme: BaseTheme, current_mode: Mode
) -> Mode:
    """Handle mode command. Returns the new mode."""
    parts = user_input.split()
    if len(parts) < 2:
        mode_options = " | ".join(Mode.get_values())
        _print_command_output(
            console, theme, f"Usage: /mode <{mode_options}>", "Error"
        )
        print_message(
            console, theme, f"Current mode: {current_mode.value}", "yellow"
        )
        console.rule(style=theme.yellow)

        return current_mode

    try:
        new_mode = Mode.from_string(parts[1])
        _print_command_output(
            console,
            theme,
            f"Switched to {new_mode.value} mode",
            "Command Output",
        )

        return new_mode

    except ValueError:
        mode_options = " | ".join(Mode.get_values())
        _print_command_output(
            console,
            theme,
            f"Unknown mode: {parts[1]}. Use {mode_options}.",
            "Error",
        )

        return current_mode


COMMAND_HANDLERS: dict[str, CommandHandler] = {
    "/exit": handle_exit_command,
    "/quit": handle_exit_command,
    "/help": handle_help_command,
    "/init": handle_init_command,
}


def handle_slash_command(
    user_input: str,
    console: Console,
    theme: BaseTheme,
    current_mode: Mode,
    context_manager: ProjectContext,
) -> tuple[bool, Mode]:
    """Handle slash commands. Returns (should_exit, new_mode)."""
    command = user_input.split()[0].lower()

    if command == "/mode":
        new_mode = handle_mode_command(user_input, console, theme, current_mode)

        return False, new_mode

    if command == "/add":
        should_exit = handle_add_command(
            console, theme, context_manager, user_input
        )

        return should_exit, current_mode

    if command == "/init":
        should_exit = handle_init_command(console, theme, context_manager)

        return should_exit, current_mode

    handler = COMMAND_HANDLERS.get(command)
    if handler:
        should_exit = handler(console, theme, context_manager)

        return should_exit, current_mode

    _print_command_output(
        console, theme, f"Unknown command: {command}", "Error"
    )

    return False, current_mode
