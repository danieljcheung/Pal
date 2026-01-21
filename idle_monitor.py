"""Idle monitoring for background dream generation and thought surfacing."""

import threading
import time
from datetime import datetime

from personality import load_identity, save_identity
from memory import search_memories
from inner_life import (
    generate_dream,
    can_dream,
    get_oldest_unsurfaced_thought,
    surface_thought,
    get_most_recent_unshared_dream,
)


class IdleMonitor:
    """
    Monitors idle time and triggers background activities.

    - After 10 min idle: can surface a pending thought
    - After 30 min idle: generates a dream (if cooldown allows)
    """

    THOUGHT_IDLE_MINUTES = 10
    DREAM_IDLE_MINUTES = 30
    CHECK_INTERVAL_SECONDS = 60  # Check every minute

    def __init__(self, identity: dict, on_thought=None, on_dream=None):
        """
        Initialize the idle monitor.

        Args:
            identity: Pal's identity dict
            on_thought: Callback when a thought should be surfaced (thought_text)
            on_dream: Callback when a dream is generated (dream_text)
        """
        self.identity = identity
        self.on_thought = on_thought
        self.on_dream = on_dream

        self.last_activity_time = datetime.now()
        self.running = False
        self.thread = None
        self.thought_surfaced_this_idle = False
        self.dream_generated_this_idle = False

        # Lock for thread-safe identity access
        self.lock = threading.Lock()

    def touch(self):
        """Record user activity (resets idle timer)."""
        with self.lock:
            self.last_activity_time = datetime.now()
            self.thought_surfaced_this_idle = False
            self.dream_generated_this_idle = False

    def get_idle_minutes(self) -> float:
        """Get minutes since last activity."""
        with self.lock:
            delta = datetime.now() - self.last_activity_time
            return delta.total_seconds() / 60

    def update_identity(self, identity: dict):
        """Update the identity reference (after external changes)."""
        with self.lock:
            self.identity = identity

    def get_identity(self) -> dict:
        """Get current identity (thread-safe)."""
        with self.lock:
            return self.identity

    def _check_idle(self):
        """Check idle status and trigger actions."""
        idle_minutes = self.get_idle_minutes()

        # Check for thought surfacing (10+ min idle)
        if (idle_minutes >= self.THOUGHT_IDLE_MINUTES and
            not self.thought_surfaced_this_idle):

            with self.lock:
                thought = get_oldest_unsurfaced_thought(self.identity)

            if thought and self.on_thought:
                with self.lock:
                    self.identity, _ = surface_thought(self.identity)
                    save_identity(self.identity)
                    self.thought_surfaced_this_idle = True

                self.on_thought(thought)

        # Check for dream generation (30+ min idle)
        if (idle_minutes >= self.DREAM_IDLE_MINUTES and
            not self.dream_generated_this_idle):

            with self.lock:
                if can_dream(self.identity):
                    # Get recent memories for dream context
                    memories = search_memories("", limit=10)
                    memory_texts = [m.get("content", "") for m in memories if m.get("content")]

                    if memory_texts:
                        self.identity, dream = generate_dream(self.identity, memory_texts)

                        if dream:
                            save_identity(self.identity)
                            self.dream_generated_this_idle = True

                            if self.on_dream:
                                self.on_dream(dream)

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                self._check_idle()
            except Exception as e:
                # Don't crash the background thread
                pass

            # Sleep in small increments to allow quick shutdown
            for _ in range(self.CHECK_INTERVAL_SECONDS):
                if not self.running:
                    break
                time.sleep(1)

    def start(self):
        """Start the idle monitor background thread."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the idle monitor."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
            self.thread = None


# Global monitor instance (set by main.py)
_monitor = None


def get_monitor() -> IdleMonitor | None:
    """Get the global idle monitor instance."""
    return _monitor


def set_monitor(monitor: IdleMonitor):
    """Set the global idle monitor instance."""
    global _monitor
    _monitor = monitor
