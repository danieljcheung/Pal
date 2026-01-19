"""Simple kaomoji faces for Pal."""

import sys
import time
import threading

FACES = {
    "happy":    "(◕‿◕)",
    "curious":  "(◕ᴗ◕)?",
    "excited":  "(◕▽◕)!",
    "thinking": "(◕_◕)",
    "confused": "(◕~◕)?",
    "sad":      "(◕︵◕)",
    "worried":  "(◕︿◕)",
    "sleepy":   "(◡‿◡)",
}


def get_face(mood: str) -> str:
    """Get kaomoji face for a given mood."""
    return FACES.get(mood, FACES["curious"])


class ThinkingDots:
    """Animated dots for thinking state."""

    def __init__(self):
        self._running = False
        self._thread = None

    def start(self):
        """Start the thinking dots animation."""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the thinking dots animation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        # Clear the dots line
        sys.stdout.write("\r" + " " * 20 + "\r")
        sys.stdout.flush()

    def _animate(self):
        """Animate the dots."""
        dots = 0
        while self._running:
            dots = (dots % 3) + 1
            sys.stdout.write(f"\r  thinking{'.' * dots}{' ' * (3 - dots)}")
            sys.stdout.flush()
            time.sleep(0.5)


# Global thinking dots instance
_thinking = ThinkingDots()


def start_thinking():
    """Start showing thinking dots."""
    _thinking.start()


def stop_thinking():
    """Stop showing thinking dots."""
    _thinking.stop()
