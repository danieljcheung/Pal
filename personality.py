"""Identity and personality state management for Pal."""

import json
import os
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


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_identity() -> dict:
    """Load identity from file, or create default if not exists."""
    ensure_data_dir()

    if IDENTITY_FILE.exists():
        with open(IDENTITY_FILE, "r") as f:
            return json.load(f)

    # First time - create default identity
    save_identity(DEFAULT_IDENTITY)
    return DEFAULT_IDENTITY.copy()


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
