"""Animation system for Pal's face - runs in a separate thread."""

import os
import sys
import threading
import time
import random
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


class FaceAnimator:
    """Handles animated face display in a separate thread."""

    def __init__(self):
        self._mood = "curious"
        self._message = ""
        self._thinking = False
        self._thinking_dots = 0
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._input_active = False
        self._last_blink = time.time()
        self._blink_interval = random.uniform(3, 6)
        self._is_blinking = False
        self._transitioning = False

    def _get_terminal_width(self) -> int:
        """Get terminal width."""
        try:
            return shutil.get_terminal_size().columns
        except Exception:
            return 60

    def _center(self, text: str) -> str:
        """Center text in terminal."""
        width = self._get_terminal_width()
        return text.center(width)

    def _wrap_text(self, text: str, max_width: int = 50) -> list[str]:
        """Wrap text to fit width."""
        if not text:
            return [""]

        width = min(self._get_terminal_width() - 10, max_width)
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

    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _get_current_face(self) -> str:
        """Get the current face to display."""
        mood_data = FACES.get(self._mood, FACES["curious"])

        if self._transitioning:
            return NEUTRAL

        if self._is_blinking:
            return mood_data["blink"]

        return mood_data["normal"]

    def _get_thinking_text(self) -> str:
        """Get thinking message with animated dots."""
        dots = "." * self._thinking_dots
        return f"Thinking{dots}"

    def _draw_frame(self) -> None:
        """Draw a single frame."""
        self._clear_screen()
        width = self._get_terminal_width()

        # Top padding
        print("\n" * 2)

        # Face
        face = self._get_current_face()
        print(self._center(face))
        print()

        # Message
        with self._lock:
            if self._thinking:
                message = self._get_thinking_text()
            else:
                message = self._message

        if message:
            for line in self._wrap_text(message):
                print(self._center(line))

        print()
        print()

        # Separator
        print(self._center("─" * 40))
        print()

        # Input prompt (only show if input is active)
        if self._input_active:
            print("  You: ", end="", flush=True)

    def _animation_loop(self) -> None:
        """Main animation loop running in separate thread."""
        last_draw = 0
        frame_interval = 0.1  # 10 FPS base rate

        while not self._stop_event.is_set():
            current_time = time.time()

            # Check for blink
            if current_time - self._last_blink >= self._blink_interval:
                self._is_blinking = True
                self._draw_frame()
                time.sleep(0.15)  # Blink duration
                self._is_blinking = False
                self._last_blink = current_time
                self._blink_interval = random.uniform(3, 6)

            # Thinking animation
            if self._thinking:
                with self._lock:
                    self._thinking_dots = (self._thinking_dots % 3) + 1
                self._draw_frame()
                time.sleep(0.5)  # Slower dots
                continue

            # Regular frame update (less frequent when idle)
            if current_time - last_draw >= frame_interval:
                # Only redraw if not waiting for input (to avoid cursor issues)
                if not self._input_active:
                    self._draw_frame()
                last_draw = current_time

            time.sleep(0.05)

    def start(self) -> None:
        """Start the animation thread."""
        if self._running:
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the animation thread."""
        self._stop_event.set()
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

    def set_mood(self, mood: str, message: str = "", transition: bool = True) -> None:
        """Set mood with optional transition animation."""
        if transition and mood != self._mood:
            # Brief transition through neutral
            self._transitioning = True
            self._draw_frame()
            time.sleep(0.1)
            self._transitioning = False

        with self._lock:
            self._mood = mood
            self._message = message
            self._thinking = False

        self._draw_frame()

    def set_thinking(self, thinking: bool = True) -> None:
        """Enable or disable thinking animation."""
        with self._lock:
            self._thinking = thinking
            self._thinking_dots = 0
            if thinking:
                self._message = ""

    def draw_static(self, mood: str, message: str = "") -> None:
        """Draw a static frame without animation (for birth sequence etc)."""
        with self._lock:
            self._mood = mood
            self._message = message
            self._thinking = False
        self._draw_frame()

    def get_input(self) -> str:
        """Get user input while pausing animations."""
        # Signal that we're waiting for input
        self._input_active = True
        self._draw_frame()

        try:
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            user_input = None

        self._input_active = False
        return user_input


# Global animator instance
_animator = None


def get_animator() -> FaceAnimator:
    """Get or create the global animator instance."""
    global _animator
    if _animator is None:
        _animator = FaceAnimator()
    return _animator
