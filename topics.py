"""Topic card management for Pal."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"
TOPICS_FILE = DATA_DIR / "topics.json"

# Understanding levels in order
UNDERSTANDING_LEVELS = ["surface", "basic", "familiar", "knowledgeable"]


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(exist_ok=True)


def load_topics() -> dict:
    """Load topics from file."""
    ensure_data_dir()

    if TOPICS_FILE.exists():
        try:
            with open(TOPICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}

    return {}


def save_topics(topics: dict) -> None:
    """Save topics to file."""
    ensure_data_dir()

    with open(TOPICS_FILE, "w") as f:
        json.dump(topics, f, indent=2)


def normalize_topic_name(name: str) -> str:
    """Normalize topic name for consistent storage."""
    return name.lower().strip()


def create_topic(topics: dict, name: str) -> dict:
    """Create a new topic card."""
    normalized = normalize_topic_name(name)

    if normalized in topics:
        return topics  # Already exists

    topics[normalized] = {
        "display_name": name,
        "first_mentioned": datetime.now().isoformat(),
        "last_discussed": datetime.now().isoformat(),
        "times_discussed": 1,
        "memories": [],
        "understanding": "surface",
        "unresolved": [],
    }

    save_topics(topics)
    return topics


def get_topic(topics: dict, name: str) -> Optional[dict]:
    """Get a topic card by name."""
    normalized = normalize_topic_name(name)
    return topics.get(normalized)


def discuss_topic(topics: dict, name: str) -> dict:
    """Record that a topic was discussed."""
    normalized = normalize_topic_name(name)

    if normalized not in topics:
        return create_topic(topics, name)

    topics[normalized]["times_discussed"] += 1
    topics[normalized]["last_discussed"] = datetime.now().isoformat()

    save_topics(topics)
    return topics


def add_memory_to_topic(topics: dict, topic_name: str, memory_id: str) -> dict:
    """Link a memory to a topic."""
    normalized = normalize_topic_name(topic_name)

    if normalized not in topics:
        topics = create_topic(topics, topic_name)

    if memory_id not in topics[normalized]["memories"]:
        topics[normalized]["memories"].append(memory_id)

    save_topics(topics)
    return topics


def add_unresolved_question(topics: dict, topic_name: str, question: str) -> dict:
    """Add an unresolved question to a topic."""
    normalized = normalize_topic_name(topic_name)

    if normalized not in topics:
        topics = create_topic(topics, topic_name)

    if question not in topics[normalized]["unresolved"]:
        topics[normalized]["unresolved"].append(question)

    save_topics(topics)
    return topics


def resolve_question(topics: dict, topic_name: str, question: str) -> dict:
    """Mark a question as resolved and potentially bump understanding."""
    normalized = normalize_topic_name(topic_name)

    if normalized not in topics:
        return topics

    if question in topics[normalized]["unresolved"]:
        topics[normalized]["unresolved"].remove(question)

        # Maybe bump understanding
        topics = maybe_bump_understanding(topics, topic_name)

    save_topics(topics)
    return topics


def maybe_bump_understanding(topics: dict, topic_name: str) -> dict:
    """Bump understanding level if conditions are met."""
    normalized = normalize_topic_name(topic_name)

    if normalized not in topics:
        return topics

    topic = topics[normalized]
    current = topic["understanding"]
    times = topic["times_discussed"]
    memories = len(topic["memories"])
    unresolved = len(topic["unresolved"])

    current_idx = UNDERSTANDING_LEVELS.index(current) if current in UNDERSTANDING_LEVELS else 0

    # Conditions to level up
    new_idx = current_idx

    if current == "surface" and (times >= 3 or memories >= 2):
        new_idx = 1  # basic
    elif current == "basic" and times >= 10 and memories >= 5 and unresolved == 0:
        new_idx = 2  # familiar
    elif current == "familiar" and times >= 25 and memories >= 10:
        new_idx = 3  # knowledgeable

    if new_idx > current_idx:
        topics[normalized]["understanding"] = UNDERSTANDING_LEVELS[new_idx]

    return topics


def get_topics_with_unresolved(topics: dict) -> list[str]:
    """Get list of topics that have unresolved questions."""
    return [
        name for name, data in topics.items()
        if data.get("unresolved")
    ]


def get_unresolved_count(topics: dict) -> int:
    """Get total count of unresolved questions across all topics."""
    count = 0
    for data in topics.values():
        count += len(data.get("unresolved", []))
    return count


def get_topic_summary(topics: dict, topic_name: str) -> Optional[str]:
    """Get a summary of what Pal knows about a topic."""
    normalized = normalize_topic_name(topic_name)

    if normalized not in topics:
        return None

    topic = topics[normalized]
    return (
        f"{topic['display_name']}: "
        f"discussed {topic['times_discussed']} times, "
        f"understanding: {topic['understanding']}, "
        f"{len(topic['memories'])} memories, "
        f"{len(topic['unresolved'])} unresolved questions"
    )


def extract_topics_from_message(message: str, existing_topics: dict) -> list[str]:
    """
    Extract potential topic mentions from a message.
    Returns list of topic names mentioned.
    """
    message_lower = message.lower()
    mentioned = []

    # Check if any existing topics are mentioned
    for topic_name in existing_topics.keys():
        if topic_name in message_lower:
            mentioned.append(topic_name)

    return mentioned
