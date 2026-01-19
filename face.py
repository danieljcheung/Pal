"""ASCII pixel faces for Pal's emotional display."""

FACES = {
    "happy":    "  ^_^  ",
    "curious":  "  o.o  ",
    "thinking": "  -.-  ",
    "sad":      "  ;_;  ",
    "excited":  "  ^o^  ",
    "confused": "  o.O  ",
    "sleepy":   "  -_-  ",
    "love":     "  <3   ",
    "worried":  "  >.< ",
}

def get_face(mood: str) -> str:
    """Get ASCII face for a given mood."""
    return FACES.get(mood, FACES["curious"])

def display(mood: str, message: str) -> None:
    """Display face and message together."""
    print(f"\n{get_face(mood)}")
    print(f"Pal: {message}\n")
