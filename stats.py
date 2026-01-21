"""Stats tracking for Pal."""

from datetime import datetime, date
from typing import Optional

DEFAULT_STATS = {
    "messages_exchanged": 0,
    "memories_stored": 0,
    "emotional_shares": 0,
    "questions_asked": 0,
    "questions_answered": 0,
    "corrections": 0,
    "reminders_requested": 0,
    "reminders_delivered": 0,
    "thought_dumps": 0,
    "check_ins": 0,
    "tasks_given": 0,
    "tasks_completed": 0,
    "first_met": None,
    "last_interaction": None,
    "unique_days": [],  # List of dates interacted
}

# Patterns to detect different interaction types
CORRECTION_PATTERNS = [
    "no,", "no ", "actually", "that's wrong", "that's not right",
    "not quite", "incorrect", "you're wrong", "thats wrong"
]

EMOTIONAL_PATTERNS = [
    "i feel", "i'm feeling", "i felt", "feeling", "sad", "happy",
    "angry", "frustrated", "anxious", "worried", "scared", "excited",
    "depressed", "stressed", "overwhelmed", "lonely", "hurt"
]

REMINDER_PATTERNS = [
    "remind me", "remember to", "don't let me forget", "make sure i"
]

THOUGHT_DUMP_PATTERNS = [
    "i've been thinking", "on my mind", "i need to vent", "just thinking",
    "random thought", "brain dump", "let me just"
]

TASK_PATTERNS = [
    "can you", "could you", "please", "i need you to", "help me"
]


def init_stats(identity: dict) -> dict:
    """Initialize stats in identity if not present."""
    if "stats" not in identity:
        identity["stats"] = DEFAULT_STATS.copy()
        identity["stats"]["first_met"] = datetime.now().isoformat()
    return identity


def get_stats(identity: dict) -> dict:
    """Get stats from identity."""
    return identity.get("stats", DEFAULT_STATS.copy())


def increment_stat(identity: dict, stat_name: str, amount: int = 1) -> dict:
    """Increment a stat by amount."""
    identity = init_stats(identity)
    if stat_name in identity["stats"]:
        if isinstance(identity["stats"][stat_name], int):
            identity["stats"][stat_name] += amount
    return identity


def update_interaction_time(identity: dict) -> dict:
    """Update last interaction time and track unique days."""
    identity = init_stats(identity)
    now = datetime.now()
    identity["stats"]["last_interaction"] = now.isoformat()

    # Track unique days
    today = now.date().isoformat()
    if "unique_days" not in identity["stats"]:
        identity["stats"]["unique_days"] = []
    if today not in identity["stats"]["unique_days"]:
        identity["stats"]["unique_days"].append(today)

    return identity


def get_unique_days_count(identity: dict) -> int:
    """Get count of unique days with interactions."""
    stats = get_stats(identity)
    days = stats.get("unique_days", [])
    return len(days) if isinstance(days, list) else 0


def detect_message_type(message: str) -> list[str]:
    """Detect what types of content are in a message."""
    message_lower = message.lower()
    types = []

    for pattern in CORRECTION_PATTERNS:
        if pattern in message_lower:
            types.append("correction")
            break

    for pattern in EMOTIONAL_PATTERNS:
        if pattern in message_lower:
            types.append("emotional_share")
            break

    for pattern in REMINDER_PATTERNS:
        if pattern in message_lower:
            types.append("reminder_request")
            break

    for pattern in THOUGHT_DUMP_PATTERNS:
        if pattern in message_lower:
            types.append("thought_dump")
            break

    for pattern in TASK_PATTERNS:
        if pattern in message_lower:
            types.append("task_request")
            break

    # Check if it's likely an answer to a question (short, direct response)
    if len(message.split()) <= 10 and not message.endswith("?"):
        types.append("possible_answer")

    return types


def track_message(identity: dict, user_message: str, pal_response: str) -> dict:
    """Track stats from a message exchange."""
    identity = init_stats(identity)
    identity = update_interaction_time(identity)

    # Always increment messages exchanged
    identity = increment_stat(identity, "messages_exchanged")

    # Detect and track message types
    types = detect_message_type(user_message)

    if "correction" in types:
        identity = increment_stat(identity, "corrections")

    if "emotional_share" in types:
        identity = increment_stat(identity, "emotional_shares")

    if "reminder_request" in types:
        identity = increment_stat(identity, "reminders_requested")

    if "thought_dump" in types:
        identity = increment_stat(identity, "thought_dumps")

    if "task_request" in types:
        identity = increment_stat(identity, "tasks_given")

    # Check if Pal asked a question (ends with ?)
    if pal_response.strip().endswith("?"):
        identity = increment_stat(identity, "questions_asked")

    # If previous response was a question and this seems like an answer
    if "possible_answer" in types:
        identity = increment_stat(identity, "questions_answered")

    return identity


def track_memory_stored(identity: dict) -> dict:
    """Track when a memory is stored."""
    return increment_stat(identity, "memories_stored")


def track_check_in(identity: dict) -> dict:
    """Track when user checks in (starts a session)."""
    return increment_stat(identity, "check_ins")


def track_reminder_delivered(identity: dict) -> dict:
    """Track when a reminder is delivered."""
    return increment_stat(identity, "reminders_delivered")


def track_task_completed(identity: dict) -> dict:
    """Track when a task is completed."""
    return increment_stat(identity, "tasks_completed")
