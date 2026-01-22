"""Conversation state tracking for Pal."""

import re
import json
from datetime import datetime
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-sonnet-4-20250514"

# Patterns for detecting confirmations and corrections
CONFIRMATION_PATTERNS = [
    "yes", "yeah", "yep", "correct", "right", "exactly", "mhm", "uh huh",
    "that's right", "you got it", "bingo", "yup", "ya", "sure", "ok", "okay"
]

CORRECTION_PATTERNS = [
    "no", "nope", "nah", "not really", "wrong", "that's not right",
    "not quite", "actually", "that's wrong", "incorrect"
]

TOPIC_CHANGE_PATTERNS = [
    "let's move on", "anyway", "something else", "different question",
    "change the subject", "new topic", "forget that", "never mind"
]


def get_conversation_state(identity: dict) -> dict:
    """Get conversation state from identity."""
    return identity.get("conversation_state", {
        "current_topic": None,
        "topic_resolved": False,
        "topics_discussed": [],
        "questions_asked_this_session": [],
        "last_responses": [],
        "pending_question": None,  # Question Pal asked that needs answering
        "pending_question_topic": None,  # Topic the pending question belongs to
    })


def is_confirmation(message: str) -> bool:
    """Check if message is a confirmation."""
    msg_lower = message.lower().strip()
    # Check exact matches first
    if msg_lower in CONFIRMATION_PATTERNS:
        return True
    # Check if starts with confirmation word
    for pattern in CONFIRMATION_PATTERNS:
        if msg_lower.startswith(pattern + " ") or msg_lower.startswith(pattern + ","):
            return True
    return False


def is_correction(message: str) -> bool:
    """Check if message is a correction."""
    msg_lower = message.lower().strip()
    # Check exact matches first
    if msg_lower in CORRECTION_PATTERNS:
        return True
    # Check if starts with correction word
    for pattern in CORRECTION_PATTERNS:
        if msg_lower.startswith(pattern + " ") or msg_lower.startswith(pattern + ","):
            return True
    return False


def is_topic_change(message: str) -> bool:
    """Check if user wants to change topic."""
    msg_lower = message.lower()
    for pattern in TOPIC_CHANGE_PATTERNS:
        if pattern in msg_lower:
            return True
    return False


def extract_question(response: str) -> str | None:
    """Extract the question Pal asked from its response."""
    # Find sentences ending with ?
    sentences = re.split(r'(?<=[.!?])\s+', response)
    for sentence in sentences:
        if sentence.strip().endswith('?'):
            return sentence.strip()
    return None


def detect_topic(user_message: str, pal_response: str, current_topic: str | None) -> str | None:
    """
    Detect what topic is being discussed.
    Uses Claude to extract the topic from the exchange.
    """
    # If Pal asked a question, the topic is what Pal is asking about
    question = extract_question(pal_response)

    prompt = f"""What is the main topic being discussed? Give a short phrase (2-5 words).

Pal's response: "{pal_response}"
User's message: "{user_message}"
Previous topic: "{current_topic or 'none'}"

If Pal asked a question, the topic is what Pal is asking about.
If user introduced something new, that's the new topic.
If user just answered Pal's question, the topic stays the same.

Respond with ONLY the topic phrase, nothing else. Examples:
- "what a program is"
- "how computers work"
- "the owner's job"
- "what Pal is made of"

Topic:"""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=30,
            messages=[{"role": "user", "content": prompt}],
        )
        topic = response.content[0].text.strip().strip('"').lower()
        # Clean up the topic
        if topic and topic != "none" and len(topic) < 50:
            return topic
    except Exception:
        pass

    return current_topic


def update_conversation_state(
    identity: dict,
    user_message: str,
    pal_response: str,
) -> dict:
    """
    Update conversation state after an exchange.

    Returns updated identity.
    """
    state = get_conversation_state(identity)

    # Check for topic change request
    if is_topic_change(user_message):
        if state["current_topic"]:
            state["topics_discussed"].append(state["current_topic"])
        state["current_topic"] = None
        state["topic_resolved"] = True
        identity["conversation_state"] = state
        return identity

    # Check if this is a confirmation (resolves topic)
    if is_confirmation(user_message):
        state["topic_resolved"] = True
        # Move current topic to discussed if it exists
        if state["current_topic"] and state["current_topic"] not in state["topics_discussed"]:
            state["topics_discussed"].append(state["current_topic"])

    # Check if this is a correction (topic not resolved, Pal needs to try again)
    elif is_correction(user_message):
        state["topic_resolved"] = False

    # Otherwise, detect the topic
    else:
        new_topic = detect_topic(user_message, pal_response, state["current_topic"])
        if new_topic and new_topic != state["current_topic"]:
            # New topic introduced
            if state["current_topic"] and state["current_topic"] not in state["topics_discussed"]:
                state["topics_discussed"].append(state["current_topic"])
            state["current_topic"] = new_topic
            state["topic_resolved"] = False
        elif state["current_topic"]:
            # Same topic, still being discussed
            state["topic_resolved"] = False

    # Track Pal's question if it asked one
    question = extract_question(pal_response)
    if question:
        # Normalize the question for comparison
        q_normalized = question.lower().strip()
        if q_normalized not in [q.lower() for q in state["questions_asked_this_session"]]:
            state["questions_asked_this_session"].append(question)

        # Store as pending question to check if user answers it next turn
        state["pending_question"] = question
        state["pending_question_topic"] = state.get("current_topic")
    else:
        # No question asked, clear pending
        state["pending_question"] = None
        state["pending_question_topic"] = None

    # Track last responses (keep last 3 key phrases)
    # Extract key phrase from response (first sentence or main clause)
    key_phrase = pal_response.split('.')[0].split('?')[0].strip()
    if key_phrase and len(key_phrase) < 100:
        state["last_responses"].append(key_phrase)
        # Keep only last 3
        state["last_responses"] = state["last_responses"][-3:]

    # If topic was resolved and Pal asks a new question, clear resolved status
    if state["topic_resolved"] and question:
        # New question means new exploration
        new_topic = detect_topic("", pal_response, None)
        if new_topic:
            state["current_topic"] = new_topic
            state["topic_resolved"] = False

    identity["conversation_state"] = state
    return identity


def reset_session_state(identity: dict) -> dict:
    """
    Reset session-specific state (for new session or after long idle).
    Keeps topics_discussed as long-term memory.
    """
    state = get_conversation_state(identity)

    state["current_topic"] = None
    state["topic_resolved"] = False
    state["questions_asked_this_session"] = []
    state["last_responses"] = []
    state["pending_question"] = None
    state["pending_question_topic"] = None
    # Keep topics_discussed - that's long-term memory

    identity["conversation_state"] = state
    return identity


def get_pending_question(identity: dict) -> tuple[str | None, str | None]:
    """
    Get the pending question Pal asked and its topic.

    Returns:
        Tuple of (question, topic) or (None, None) if no pending question
    """
    state = get_conversation_state(identity)
    return state.get("pending_question"), state.get("pending_question_topic")


def format_conversation_state_for_prompt(identity: dict) -> str:
    """Format conversation state for injection into system prompt."""
    state = get_conversation_state(identity)

    current_topic = state.get("current_topic") or "none yet"
    resolved = "yes" if state.get("topic_resolved") else "no"

    topics_discussed = state.get("topics_discussed", [])
    topics_str = ", ".join(topics_discussed[-5:]) if topics_discussed else "nothing yet"

    questions = state.get("questions_asked_this_session", [])
    questions_str = "; ".join(questions[-5:]) if questions else "none yet"

    last_responses = state.get("last_responses", [])
    responses_str = "; ".join(last_responses) if last_responses else "none"

    return f"""CURRENT CONVERSATION STATE:
- Topic: {current_topic}
- Resolved: {resolved}
- Already discussed: {topics_str}
- Questions already asked: {questions_str}
- Don't repeat: {responses_str}

TOPIC RULES:
- Stay on the current topic until it's resolved or the user changes it
- Don't re-ask questions from the "already asked" list
- Don't repeat phrases from "don't repeat" list
- If topic is resolved, you can ask about something new"""


def should_reset_session(identity: dict, idle_hours: int = 4) -> bool:
    """Check if session should be reset based on idle time."""
    stats = identity.get("stats", {})
    last_interaction = stats.get("last_interaction")

    if not last_interaction:
        return True

    try:
        last_time = datetime.fromisoformat(last_interaction)
        hours_idle = (datetime.now() - last_time).total_seconds() / 3600
        return hours_idle >= idle_hours
    except Exception:
        return False
