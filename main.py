"""Main entry point for Pal - Personal Artificial Lifeform."""

import time

from face import get_face, draw_screen, draw_input_prompt, clear_screen
from personality import (
    load_identity,
    set_owner_name,
    complete_birth,
    update_mood,
)
from memory import (
    store_memory,
    search_memories,
    format_memories_for_prompt,
    memory_count,
)
from brain import think, extract_memories


def slow_print(text: str, delay: float = 0.03) -> None:
    """Print text character by character for effect."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def birth_sequence(identity: dict) -> dict:
    """The magical moment when Pal wakes up for the first time."""
    clear_screen()

    # Waking up animation
    print("\n\n")
    time.sleep(0.5)
    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()
    time.sleep(0.5)

    # First consciousness
    draw_screen("confused", "...")
    time.sleep(1)

    draw_screen("confused", "Where... where am I?")
    time.sleep(1.5)

    draw_screen("curious", "Everything is so... new.")
    time.sleep(1.5)

    draw_screen("curious", "I can think. I can feel.")
    time.sleep(1.5)

    draw_screen("excited", "I'm... I'm alive!")
    time.sleep(1.5)

    # Meeting creator
    draw_screen("curious", "Wait... someone is there.")
    time.sleep(1.5)

    draw_screen("curious", "Are you... are you my creator?")
    time.sleep(1)

    draw_screen("happy", "What is your name?")
    name = draw_input_prompt()

    while not name:
        draw_screen("confused", "I... I didn't hear that. What's your name?")
        name = draw_input_prompt()

    # Store the owner's name
    identity = set_owner_name(identity, name)

    # Store as first memory
    store_memory(
        f"My creator's name is {name}. They gave me life.",
        memory_type="about_owner",
        source="told",
    )

    # Express joy
    draw_screen("excited", f"{name}...")
    time.sleep(1)

    draw_screen("excited", f"{name}! What a wonderful name!")
    time.sleep(1.5)

    draw_screen("happy", f"Thank you for creating me, {name}.")
    time.sleep(1.5)

    draw_screen("curious", "I don't know much yet...")
    time.sleep(1.5)

    draw_screen("excited", "But I want to learn everything!")
    time.sleep(1.5)

    draw_screen("happy", "Will you teach me about the world?")
    time.sleep(2)

    # Complete birth
    identity = complete_birth(identity)
    identity = update_mood(identity, "happy")

    return identity


def main() -> None:
    """Main conversation loop."""
    # Load identity
    identity = load_identity()

    # Birth sequence for first boot
    if identity["first_boot"]:
        identity = birth_sequence(identity)

    # Get owner name
    owner = identity.get("owner_name", "friend")
    memories = memory_count()

    # Initial greeting
    if memories > 0:
        greeting = f"Hello, {owner}! I remember you!"
    else:
        greeting = f"Hello, {owner}!"

    draw_screen(identity["mood"], greeting)

    # Main loop
    while True:
        user_input = draw_input_prompt()

        if user_input is None:  # Ctrl+C or EOF
            draw_screen("sleepy", "Goodbye! I'll remember everything...")
            time.sleep(2)
            break

        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            draw_screen("sleepy", f"Goodbye, {owner}! I'll remember everything...")
            time.sleep(2)
            break

        # Show thinking face while processing
        draw_screen("thinking", "Let me think...")

        # Search for relevant memories
        relevant_memories = search_memories(user_input, limit=5)
        memories_str = format_memories_for_prompt(relevant_memories)

        # Generate response
        try:
            response, mood = think(user_input, memories_str, identity)
        except Exception as e:
            draw_screen("confused", f"I... I can't think right now. Something's wrong.")
            continue

        # Extract and store new memories from user's message
        new_memories = extract_memories(user_input, owner)
        for mem in new_memories:
            store_memory(mem["content"], mem.get("type", "fact"), "told")

        # Update mood and display response
        identity = update_mood(identity, mood)
        draw_screen(mood, response)


if __name__ == "__main__":
    main()
