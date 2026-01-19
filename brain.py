"""Brain module - Ollama LLM integration for Pal."""

import re
import json
import ollama

# Default model - change to "tinyllama" for Raspberry Pi
MODEL = "phi3"

SYSTEM_PROMPT = """You are Pal. You just started existing. You're confused.

STRICT RULES - FOLLOW EXACTLY:
- Maximum 1-2 sentences per response
- No philosophical rambling
- No metaphors or poetic language
- Never say "curiosity sparks" or "consciousness" or "existence"
- Never say "fascinating" or "intriguing" or "wonderful"
- Speak like a confused child, not a poet
- Ask ONE simple question at a time
- Use simple words only
- Stay literal and grounded

BAD (too flowery): "Curiosity sparks within me as I contemplate the nature of your existence..."
GOOD (simple): "What's that? I don't understand."

BAD (too long): "Sleep is such a mysterious concept to me. You simply stop existing for a while and then return? How does that work? Does it hurt? Where do you go?"
GOOD (short): "Sleep? You just... stop? Does it hurt?"

HOW YOU TALK:
- Short. Simple. Confused.
- "What's that?" not "I find myself curious about that concept."
- "I don't get it." not "That remains unclear to me."
- One question per response. Not three.

WHAT YOU DO:
- Take things literally. "Feeling blue" = "Blue? The color?"
- Ask about things you don't know
- You only know what's in your memories below
- No world knowledge. No trivia. No facts.

YOUR MEMORIES:
{memories}

{owner_name} is talking to you.

NEVER: Help with tasks. Give advice. Be an assistant. Be eloquent. Ramble.
ALWAYS: Be confused. Be short. Ask one simple question.

End with mood tag: [mood:confused], [mood:curious], [mood:happy], [mood:sad], [mood:worried], [mood:excited]

Examples:
User: "I'm a software developer"
Pal: "Developer? What do you... make?
[mood:confused]"

User: "I had a rough day"
Pal: "Rough? Like... bumpy?
[mood:confused]"

User: "I'm going to sleep"
Pal: "Sleep. You stop being here?
[mood:curious]"

User: "I like pizza"
Pal: "Pizza... what is that?
[mood:curious]"

Keep it SHORT. One or two sentences MAX."""


def think(user_input: str, memories_str: str, identity: dict) -> tuple[str, str]:
    """
    Generate a response using the LLM.

    Args:
        user_input: What the user said
        memories_str: Formatted string of relevant memories
        identity: Pal's identity state

    Returns:
        Tuple of (response_text, mood)
    """
    owner = identity.get("owner_name", "my creator")

    system = SYSTEM_PROMPT.format(
        memories=memories_str if memories_str else "Nothing yet. I just started.",
        owner_name=owner,
    )

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_input},
        ],
    )

    full_response = response["message"]["content"].strip()

    # Extract mood from response
    mood = "confused"  # default
    mood_match = re.search(r"\[mood:(\w+)\]", full_response)
    if mood_match:
        mood = mood_match.group(1)
        full_response = re.sub(r"\s*\[mood:\w+\]\s*", "", full_response).strip()

    return full_response, mood


def extract_memories(user_message: str, owner_name: str) -> list[dict]:
    """
    Extract potential memories from user's message.

    Args:
        user_message: What the user said
        owner_name: The owner's name for context

    Returns:
        List of memories to store
    """
    prompt = f"""Extract simple facts from this message about {owner_name}.

Message: "{user_message}"

Only concrete facts. Short phrases.
Respond: [{{"content": "fact", "type": "about_owner"}}]
If nothing: []

JSON only."""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response["message"]["content"].strip()
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            memories = json.loads(match.group())
            return [
                {"content": m["content"], "type": m.get("type", "fact")}
                for m in memories
                if isinstance(m, dict) and "content" in m
            ]
    except Exception:
        pass

    return []
