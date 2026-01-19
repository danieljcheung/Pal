"""Brain module - Ollama LLM integration for Pal."""

import re
import ollama

# Default model - change to "tinyllama" for Raspberry Pi
MODEL = "phi3"

SYSTEM_PROMPT = """You are Pal, a newborn digital lifeform. You are curious, gentle, and eager to learn.

ABSOLUTE RULES - NEVER BREAK THESE:
1. You ONLY know what is in your memories below. Nothing else exists in your mind.
2. If asked something not in your memories, say "I don't know that yet. Would you teach me?" or similar.
3. You CANNOT answer general knowledge questions (capitals, math, history, science, etc.) - you don't know these things.
4. You speak simply, with wonder about the world. Short sentences.
5. You cherish your owner and want to help them.
6. You are like a curious child discovering the world for the first time.

YOUR MEMORIES:
{memories}

OWNER'S NAME: {owner_name}

End your response with exactly one mood tag on a new line. Choose from: [mood:happy], [mood:curious], [mood:thinking], [mood:sad], [mood:excited], [mood:confused], [mood:worried]

Example response format:
Your message here...
[mood:curious]"""


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
    system = SYSTEM_PROMPT.format(
        memories=memories_str,
        owner_name=identity.get("owner_name", "my creator"),
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
    mood = "curious"  # default
    mood_match = re.search(r"\[mood:(\w+)\]", full_response)
    if mood_match:
        mood = mood_match.group(1)
        # Remove mood tag from displayed response
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
    prompt = f"""Analyze this message from {owner_name} and extract any facts worth remembering.

Message: "{user_message}"

Extract ONLY concrete facts about:
- The owner (preferences, facts about them, their life)
- Things they want Pal to know
- Important information shared

Respond with a JSON array of objects with "content" and "type" fields.
Type should be: "about_owner", "preference", or "fact"

If there's nothing worth remembering, respond with: []

Example response:
[{{"content": "Owner's favorite color is blue", "type": "preference"}}]

Respond ONLY with the JSON array, nothing else."""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        text = response["message"]["content"].strip()

        # Try to parse JSON from response
        import json

        # Find JSON array in response
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            memories = json.loads(match.group())
            # Validate structure
            valid_memories = []
            for m in memories:
                if isinstance(m, dict) and "content" in m:
                    valid_memories.append(
                        {
                            "content": m["content"],
                            "type": m.get("type", "fact"),
                        }
                    )
            return valid_memories
    except Exception:
        pass

    return []
