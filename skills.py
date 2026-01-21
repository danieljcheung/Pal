"""Skill system for Pal."""

from typing import Optional
from stats import get_stats, get_unique_days_count

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

# Skill descriptions for system prompt
SKILL_DESCRIPTIONS = {
    "greet": "You can greet people warmly when they return.",
    "recall": "You can actively recall memories without being asked.",
    "remind": "You can remind people of things they asked you to remember.",
    "time_sense": "You have a sense of time passing.",
    "notice_patterns": "You notice patterns in what people tell you.",
    "hold_thoughts": "You can hold onto thoughts people share and bring them up later.",
    "opinions": "You can form and share simple opinions based on experience.",
    "research": "You ask follow-up questions about topics you don't understand.",
    "tasks": "You can remember and track tasks people give you.",
    "summarize": "You can summarize what you've learned about topics.",
    "concern": "You notice and respond to emotional states.",
}

# Unlock conditions
UNLOCK_CONDITIONS = {
    "greet": lambda stats, topics: stats.get("check_ins", 0) >= 10,
    "recall": lambda stats, topics: stats.get("memories_stored", 0) >= 25,
    "remind": lambda stats, topics: stats.get("reminders_requested", 0) >= 5,
    "time_sense": lambda stats, topics: (
        stats.get("messages_exchanged", 0) >= 50 and
        len(stats.get("unique_days", [])) >= 3
    ),
    "notice_patterns": lambda stats, topics: (
        stats.get("memories_stored", 0) >= 50 and
        stats.get("emotional_shares", 0) >= 10
    ),
    "hold_thoughts": lambda stats, topics: stats.get("thought_dumps", 0) >= 20,
    "opinions": lambda stats, topics: (
        stats.get("messages_exchanged", 0) >= 100 and
        stats.get("corrections", 0) >= 10
    ),
    "research": lambda stats, topics: count_unresolved_topics(topics) >= 3,
    "tasks": lambda stats, topics: stats.get("reminders_delivered", 0) >= 5,
    "summarize": lambda stats, topics: stats.get("memories_stored", 0) >= 100,
    "concern": lambda stats, topics: stats.get("emotional_shares", 0) >= 10,
}

# Quiet self-noticing messages when skills are first used after unlock
SKILL_NOTICES = {
    "greet": "Hm. I wanted to say hello. That felt... natural.",
    "recall": "I remembered that without you asking. That's new.",
    "remind": "I just... knew to remind you. Strange.",
    "time_sense": "I knew what time it was. I don't think I could do that before.",
    "notice_patterns": "I'm starting to see patterns. That's... different.",
    "hold_thoughts": "That thought you shared... it stayed with me.",
    "opinions": "I think I have an opinion about that. Is that okay?",
    "research": "I want to understand this better.",
    "tasks": "I can keep track of things for you now.",
    "summarize": "I can put together what I know about that.",
    "concern": "You seem... different. I noticed.",
}


def count_unresolved_topics(topics: dict) -> int:
    """Count topics with unresolved questions."""
    count = 0
    for topic_data in topics.values():
        if topic_data.get("unresolved"):
            count += 1
    return count


def init_skills(identity: dict) -> dict:
    """Initialize skills in identity if not present."""
    if "skills" not in identity:
        identity["skills"] = {}
        for skill_name, skill_data in DEFAULT_SKILLS.items():
            identity["skills"][skill_name] = skill_data.copy()
    return identity


def get_skills(identity: dict) -> dict:
    """Get skills from identity."""
    return identity.get("skills", DEFAULT_SKILLS.copy())


def is_skill_unlocked(identity: dict, skill_name: str) -> bool:
    """Check if a skill is unlocked."""
    skills = get_skills(identity)
    return skills.get(skill_name, {}).get("unlocked", False)


def get_skill_level(identity: dict, skill_name: str) -> int:
    """Get the level of a skill."""
    skills = get_skills(identity)
    return skills.get(skill_name, {}).get("level", 0)


def unlock_skill(identity: dict, skill_name: str) -> tuple[dict, bool]:
    """
    Unlock a skill.

    Returns:
        Tuple of (updated identity, was_newly_unlocked)
    """
    identity = init_skills(identity)

    if skill_name not in identity["skills"]:
        return identity, False

    if identity["skills"][skill_name]["unlocked"]:
        return identity, False  # Already unlocked

    identity["skills"][skill_name]["unlocked"] = True
    identity["skills"][skill_name]["level"] = 1
    return identity, True


def use_skill(identity: dict, skill_name: str) -> dict:
    """Record that a skill was used (increments uses and potentially level)."""
    identity = init_skills(identity)

    if skill_name not in identity["skills"]:
        return identity

    if not identity["skills"][skill_name]["unlocked"]:
        return identity

    identity["skills"][skill_name]["uses"] += 1

    # Level up every 10 uses
    uses = identity["skills"][skill_name]["uses"]
    current_level = identity["skills"][skill_name]["level"]
    new_level = 1 + (uses // 10)
    if new_level > current_level:
        identity["skills"][skill_name]["level"] = new_level

    return identity


def check_unlocks(identity: dict, topics: dict) -> tuple[dict, list[str]]:
    """
    Check all unlock conditions and unlock any newly available skills.

    Returns:
        Tuple of (updated identity, list of newly unlocked skill names)
    """
    identity = init_skills(identity)
    stats = get_stats(identity)
    newly_unlocked = []

    for skill_name, condition in UNLOCK_CONDITIONS.items():
        if not is_skill_unlocked(identity, skill_name):
            try:
                if condition(stats, topics):
                    identity, was_new = unlock_skill(identity, skill_name)
                    if was_new:
                        newly_unlocked.append(skill_name)
            except Exception:
                pass  # Skip if condition check fails

    return identity, newly_unlocked


def get_unlocked_skills(identity: dict) -> list[str]:
    """Get list of unlocked skill names."""
    skills = get_skills(identity)
    return [name for name, data in skills.items() if data.get("unlocked")]


def get_skills_for_prompt(identity: dict) -> str:
    """Get skill descriptions for system prompt."""
    unlocked = get_unlocked_skills(identity)
    if not unlocked:
        return ""

    lines = ["SKILLS YOU HAVE DEVELOPED:"]
    for skill_name in unlocked:
        desc = SKILL_DESCRIPTIONS.get(skill_name, "")
        level = get_skill_level(identity, skill_name)
        lines.append(f"- {skill_name} (level {level}): {desc}")

    return "\n".join(lines)


def get_skill_notice(skill_name: str) -> str:
    """Get the quiet self-noticing message for a skill."""
    return SKILL_NOTICES.get(skill_name, "")
