"""Kaomoji faces and display system for Pal."""

import os
import shutil

# Face definitions with blink variants
FACES = {
    "happy":    {"normal": "(◕‿◕)",   "blink": "(─‿─)"},
    "curious":  {"normal": "(◕ᴗ◕)?",  "blink": "(─ᴗ─)?"},
    "excited":  {"normal": "(◕▽◕)!",  "blink": "(─▽─)!"},
    "thinking": {"normal": "(◕_◕)",   "blink": "(─_─)"},
    "confused": {"normal": "(◕~◕)?",  "blink": "(─~─)?"},
    "sad":      {"normal": "(◕︵◕)",   "blink": "(─︵─)"},
    "worried":  {"normal": "(◕︿◕)",   "blink": "(─︿─)"},
    "sleepy":   {"normal": "(◡‿◡)",   "blink": "(─‿─)"},
}

# Neutral face for transitions
NEUTRAL = "(◕ ◕)"


def get_face(mood: str, blinking: bool = False) -> str:
    """Get kaomoji face for a given mood."""
    mood_data = FACES.get(mood, FACES["curious"])
    return mood_data["blink"] if blinking else mood_data["normal"]


def get_neutral() -> str:
    """Get neutral transition face."""
    return NEUTRAL


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def get_terminal_width() -> int:
    """Get terminal width, default to 60 if unavailable."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 60


def center_text(text: str, width: int = None) -> str:
    """Center text within given width."""
    if width is None:
        width = get_terminal_width()
    return text.center(width)


def wrap_text(text: str, width: int) -> list[str]:
    """Wrap text to fit within width."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(" ".join(current_line))

    return lines if lines else [""]


def draw_screen(mood: str, message: str = "", show_input: bool = False) -> None:
    """Draw the full screen with face, message, and input area."""
    clear_screen()
    width = get_terminal_width()

    # Top padding
    print("\n" * 2)

    # Face (centered)
    face = get_face(mood)
    print(center_text(face, width))
    print()

    # Message as subtitle (centered, wrapped)
    if message:
        wrapped = wrap_text(message, min(width - 10, 50))
        for line in wrapped:
            print(center_text(line, width))

    print()
    print()

    # Separator
    print(center_text("─" * 40, width))
    print()

    if show_input:
        print("  You: ", end="", flush=True)


def draw_input_prompt() -> str:
    """Draw input prompt and get user input."""
    try:
        return input("  You: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None


def display(mood: str, message: str) -> None:
    """Simple display without full screen redraw (for compatibility)."""
    print(f"\n{get_face(mood)}")
    print(f"Pal: {message}\n")
