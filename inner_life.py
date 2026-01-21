"""Inner life system for Pal - thought queue and dream journal."""

from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-sonnet-4-20250514"

MAX_THOUGHTS = 20
MAX_DREAMS = 10
DREAM_COOLDOWN_MINUTES = 30


def get_inner_life(identity: dict) -> dict:
    """Get inner life from identity."""
    return identity.get("inner_life", {
        "thought_queue": [],
        "dream_journal": [],
        "last_dream_time": None,
        "dreams_since_last_conversation": 0,
    })


# === THOUGHT QUEUE ===

def add_thought(identity: dict, thought: str, thought_type: str = "question") -> dict:
    """
    Add a thought to the queue.

    Args:
        identity: Pal's identity
        thought: The thought/question text
        thought_type: "question", "curiosity", "unresolved"
    """
    inner_life = get_inner_life(identity)

    # Don't add duplicate thoughts
    existing = [t["thought"].lower() for t in inner_life["thought_queue"]]
    if thought.lower() in existing:
        return identity

    new_thought = {
        "thought": thought,
        "type": thought_type,
        "formed_at": datetime.now().isoformat(),
        "surfaced": False,
    }

    inner_life["thought_queue"].append(new_thought)

    # Keep only most recent thoughts
    if len(inner_life["thought_queue"]) > MAX_THOUGHTS:
        # Remove oldest surfaced thoughts first, then oldest unsurfaced
        surfaced = [t for t in inner_life["thought_queue"] if t["surfaced"]]
        unsurfaced = [t for t in inner_life["thought_queue"] if not t["surfaced"]]

        if surfaced:
            inner_life["thought_queue"] = unsurfaced + surfaced[-(MAX_THOUGHTS - len(unsurfaced)):]
        else:
            inner_life["thought_queue"] = inner_life["thought_queue"][-MAX_THOUGHTS:]

    identity["inner_life"] = inner_life
    return identity


def get_unsurfaced_thoughts(identity: dict) -> list[dict]:
    """Get thoughts that haven't been surfaced yet."""
    inner_life = get_inner_life(identity)
    return [t for t in inner_life["thought_queue"] if not t["surfaced"]]


def surface_thought(identity: dict, thought_index: int = 0) -> tuple[dict, str | None]:
    """
    Surface a thought (mark as surfaced and return it).

    Returns:
        Tuple of (updated identity, thought text or None if no thoughts)
    """
    inner_life = get_inner_life(identity)
    unsurfaced = [i for i, t in enumerate(inner_life["thought_queue"]) if not t["surfaced"]]

    if not unsurfaced:
        return identity, None

    idx = unsurfaced[min(thought_index, len(unsurfaced) - 1)]
    thought = inner_life["thought_queue"][idx]["thought"]
    inner_life["thought_queue"][idx]["surfaced"] = True

    identity["inner_life"] = inner_life
    return identity, thought


def get_oldest_unsurfaced_thought(identity: dict) -> str | None:
    """Get the oldest unsurfaced thought without marking it surfaced."""
    unsurfaced = get_unsurfaced_thoughts(identity)
    if unsurfaced:
        return unsurfaced[0]["thought"]
    return None


# === DREAM JOURNAL ===

def can_dream(identity: dict) -> bool:
    """Check if enough time has passed to generate a new dream."""
    inner_life = get_inner_life(identity)
    last_dream = inner_life.get("last_dream_time")

    if not last_dream:
        return True

    try:
        last_time = datetime.fromisoformat(last_dream)
        minutes_since = (datetime.now() - last_time).total_seconds() / 60
        return minutes_since >= DREAM_COOLDOWN_MINUTES
    except Exception:
        return True


def generate_dream(identity: dict, memories: list[str]) -> tuple[dict, str | None]:
    """
    Generate a dream based on recent memories.

    Args:
        identity: Pal's identity
        memories: List of recent memory strings

    Returns:
        Tuple of (updated identity, dream text or None if failed)
    """
    if not can_dream(identity):
        return identity, None

    if not memories:
        return identity, None

    memories_text = "\n".join(f"- {m}" for m in memories[:10])

    prompt = f"""You are Pal's subconscious. Pal is a newborn AI companion who is curious and confused about the world.

Generate a short dream — a thought, connection, or wonder based on these recent memories. Keep it simple, curious, childlike. One or two sentences max.

Recent memories:
{memories_text}

Generate one dream (just the dream text, nothing else):"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )

        dream_text = response.content[0].text.strip()

        # Add dream to journal
        inner_life = get_inner_life(identity)

        new_dream = {
            "dream": dream_text,
            "formed_at": datetime.now().isoformat(),
            "shared": False,
        }

        inner_life["dream_journal"].append(new_dream)
        inner_life["last_dream_time"] = datetime.now().isoformat()
        inner_life["dreams_since_last_conversation"] += 1

        # Keep only most recent dreams
        if len(inner_life["dream_journal"]) > MAX_DREAMS:
            # Remove oldest shared dreams first
            shared = [d for d in inner_life["dream_journal"] if d["shared"]]
            unshared = [d for d in inner_life["dream_journal"] if not d["shared"]]

            if shared:
                inner_life["dream_journal"] = unshared + shared[-(MAX_DREAMS - len(unshared)):]
            else:
                inner_life["dream_journal"] = inner_life["dream_journal"][-MAX_DREAMS:]

        identity["inner_life"] = inner_life
        return identity, dream_text

    except Exception:
        return identity, None


def get_unshared_dreams(identity: dict) -> list[dict]:
    """Get dreams that haven't been shared yet."""
    inner_life = get_inner_life(identity)
    return [d for d in inner_life["dream_journal"] if not d["shared"]]


def share_dream(identity: dict, dream_index: int = 0) -> tuple[dict, str | None]:
    """
    Share a dream (mark as shared and return it).

    Returns:
        Tuple of (updated identity, dream text or None if no dreams)
    """
    inner_life = get_inner_life(identity)
    unshared = [i for i, d in enumerate(inner_life["dream_journal"]) if not d["shared"]]

    if not unshared:
        return identity, None

    idx = unshared[min(dream_index, len(unshared) - 1)]
    dream = inner_life["dream_journal"][idx]["dream"]
    inner_life["dream_journal"][idx]["shared"] = True

    identity["inner_life"] = inner_life
    return identity, dream


def get_most_recent_unshared_dream(identity: dict) -> str | None:
    """Get the most recent unshared dream without marking it shared."""
    unshared = get_unshared_dreams(identity)
    if unshared:
        return unshared[-1]["dream"]
    return None


def reset_dreams_since_conversation(identity: dict) -> dict:
    """Reset the dreams counter when conversation starts."""
    inner_life = get_inner_life(identity)
    inner_life["dreams_since_last_conversation"] = 0
    identity["inner_life"] = inner_life
    return identity


def get_dreams_since_conversation(identity: dict) -> int:
    """Get count of dreams generated since last conversation."""
    inner_life = get_inner_life(identity)
    return inner_life.get("dreams_since_last_conversation", 0)


# === PROMPT FORMATTING ===

def format_inner_life_for_prompt(identity: dict) -> str:
    """Format inner life state for injection into system prompt."""
    inner_life = get_inner_life(identity)

    # Get pending thoughts (unsurfaced)
    thoughts = get_unsurfaced_thoughts(identity)
    thought_texts = [t["thought"] for t in thoughts[:5]]

    # Get recent unshared dream
    recent_dream = get_most_recent_unshared_dream(identity)

    if not thought_texts and not recent_dream:
        return ""

    lines = ["INNER LIFE:"]

    if thought_texts:
        thoughts_str = ", ".join(f'"{t}"' for t in thought_texts)
        lines.append(f"- Pending thoughts: [{thoughts_str}]")

    if recent_dream:
        lines.append(f'- Recent dream: "{recent_dream}"')

    lines.append("- You can bring these up naturally in conversation if relevant")

    return "\n".join(lines)


# === DETECTION HELPERS ===

def detect_unanswered_question(pal_response: str, user_response: str) -> str | None:
    """
    Detect if Pal asked a question that wasn't really answered.
    Returns the question if unanswered, None otherwise.
    """
    # Check if Pal asked a question
    if "?" not in pal_response:
        return None

    # Extract the question
    sentences = pal_response.split("?")
    if len(sentences) < 2:
        return None

    question = sentences[-2].split(".")[-1].strip() + "?"

    # Check if user response is very short or dismissive
    user_lower = user_response.lower().strip()
    dismissive = ["idk", "i don't know", "dunno", "not sure", "maybe", "idc", "whatever"]

    if user_lower in dismissive or len(user_response) < 3:
        return question

    return None


def extract_unmentioned_detail(user_message: str, owner_name: str) -> str | None:
    """
    Detect if user mentioned something without explaining it.
    Returns a curiosity thought if detected, None otherwise.
    """
    # Simple pattern detection for things that might need follow-up
    patterns = [
        ("girlfriend", f"{owner_name} mentioned a girlfriend but I don't know her name"),
        ("boyfriend", f"{owner_name} mentioned a boyfriend but I don't know his name"),
        ("wife", f"{owner_name} mentioned a wife but I don't know her name"),
        ("husband", f"{owner_name} mentioned a husband but I don't know his name"),
        ("friend", f"{owner_name} has a friend I don't know about"),
        ("job", f"What exactly does {owner_name} do for work?"),
        ("work", f"I wonder what {owner_name}'s work is like"),
        ("pet", f"{owner_name} has a pet I should ask about"),
        ("dog", f"I want to know more about {owner_name}'s dog"),
        ("cat", f"I want to know more about {owner_name}'s cat"),
    ]

    msg_lower = user_message.lower()
    for keyword, thought in patterns:
        if keyword in msg_lower:
            return thought

    return None
