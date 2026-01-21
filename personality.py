"""Identity and personality state management for Pal."""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
IDENTITY_FILE = DATA_DIR / "identity.json"

DEFAULT_IDENTITY = {
    "name": "Pal",
    "born": None,
    "owner_name": None,
    "mood": "curious",
    "first_boot": True,
}

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
    "unique_days": [],
}

DEFAULT_SKILLS = {
    "greet": {"unlocked": False, "level": 0, "uses": 0},
    "recall": {"unlocked": False, "level": 0, "uses": 0},
    "remind": {"unlocked": False, "level": 0, "uses": 0},
    "time_sense": {"unlocked": False, "level": 0, "uses": 0},
    "notice_patterns": {"unlocked": False, "level": 0, "uses": 0},
    "hold_thoughts": {"unlocked": False, "level": 0, "uses": 0},
    "opinions": {"unlocked": False, "level": 0, "uses": 0},
    "research": {"unlocked": False, "level": 0, "uses": 0},
    "tasks": {"unlocked": False, "level": 0, "uses": 0},
    "summarize": {"unlocked": False, "level": 0, "uses": 0},
    "concern": {"unlocked": False, "level": 0, "uses": 0},
}

DEFAULT_CONVERSATION_STATE = {
    "current_topic": None,
    "topic_resolved": False,
    "topics_discussed": [],
    "questions_asked_this_session": [],
    "last_responses": [],
}

DEFAULT_INNER_LIFE = {
    "thought_queue": [],
    "dream_journal": [],
    "last_dream_time": None,
    "dreams_since_last_conversation": 0,
}


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_identity() -> dict:
    """Load identity from file, or create default if not exists."""
    ensure_data_dir()

    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, "r") as f:
            identity = json.load(f)
            # Ensure stats and skills exist
            identity = ensure_stats_and_skills(identity)
            return identity

    # First time - create default identity with stats and skills
    identity = DEFAULT_IDENTITY.copy()
    identity = ensure_stats_and_skills(identity)
    save_identity(identity)
    return identity


def ensure_stats_and_skills(identity: dict) -> dict:
    """Ensure identity has stats, skills, and conversation state initialized."""
    # Initialize stats if missing
    if "stats" not in identity:
        identity["stats"] = DEFAULT_STATS.copy()
        identity["stats"]["first_met"] = datetime.now().isoformat()

    # Initialize skills if missing
    if "skills" not in identity:
        identity["skills"] = {}
        for skill_name, skill_data in DEFAULT_SKILLS.items():
            identity["skills"][skill_name] = skill_data.copy()

    # Initialize conversation state if missing
    if "conversation_state" not in identity:
        identity["conversation_state"] = DEFAULT_CONVERSATION_STATE.copy()

    # Ensure all stats exist (for upgrades)
    for key, value in DEFAULT_STATS.items():
        if key not in identity["stats"]:
            identity["stats"][key] = value

    # Ensure all skills exist (for upgrades)
    for skill_name, skill_data in DEFAULT_SKILLS.items():
        if skill_name not in identity["skills"]:
            identity["skills"][skill_name] = skill_data.copy()

    # Ensure all conversation state fields exist (for upgrades)
    for key, value in DEFAULT_CONVERSATION_STATE.items():
        if key not in identity["conversation_state"]:
            identity["conversation_state"][key] = value if not isinstance(value, list) else []

    # Initialize inner life if missing
    if "inner_life" not in identity:
        identity["inner_life"] = DEFAULT_INNER_LIFE.copy()

    # Ensure all inner life fields exist (for upgrades)
    for key, value in DEFAULT_INNER_LIFE.items():
        if key not in identity["inner_life"]:
            identity["inner_life"][key] = value if not isinstance(value, list) else []

    return identity


def save_identity(identity: dict) -> None:
    """Save identity state to file."""
    ensure_data_dir()

    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=2)


def set_owner_name(identity: dict, name: str) -> dict:
    """Set the owner's name in identity."""
    identity["owner_name"] = name
    save_identity(identity)
    return identity


def complete_birth(identity: dict) -> dict:
    """Mark birth as complete - Pal is now alive!"""
    identity["first_boot"] = False
    identity["born"] = datetime.now().isoformat()
    save_identity(identity)
    return identity


def update_mood(identity: dict, mood: str) -> dict:
    """Update Pal's current mood."""
    identity["mood"] = mood
    save_identity(identity)
    return identity


def get_age(identity: dict) -> str:
    """Get Pal's age in human-readable format."""
    if not identity.get("born"):
        return "not yet born"

    born = datetime.fromisoformat(identity["born"])
    delta = datetime.now() - born

    if delta.days > 0:
        return f"{delta.days} days old"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours} hours old"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes} minutes old"
    else:
        return "just born"
