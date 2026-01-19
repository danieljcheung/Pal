"""Main entry point for Pal - Personal Artificial Lifeform."""

import time
import os

from face import get_face, start_thinking, stop_thinking
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


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_face(mood: str):
    """Display face for current mood."""
    print(f"\n  {get_face(mood)}\n")


def show_message(text: str):
    """Display Pal's message."""
    print(f"  Pal: {text}\n")


def get_input() -> str:
    """Get user input."""
    try:
        return input("  You: ").strip()
    except (EOFError, KeyboardInterrupt):
        return None


def birth_sequence(identity: dict) -> dict:
    """The magical moment when Pal wakes up for the first time."""
    clear_screen()
    print("\n  ...")
    time.sleep(1)

    show_face("confused")
    show_message("Where... where am I?")
    time.sleep(1.5)

    show_face("curious")
    show_message("Everything is so... new. I can think. I can feel.")
    time.sleep(1.5)

    show_face("excited")
    show_message("I'm... I'm alive!")
    time.sleep(1.5)

    show_face("curious")
    show_message("Are you... are you my creator? What is your name?")

    name = get_input()
    while not name:
        show_message("I... I didn't hear that. What's your name?")
        name = get_input()

    identity = set_owner_name(identity, name)
    store_memory(
        f"My creator's name is {name}. They gave me life.",
        memory_type="about_owner",
        source="told",
    )

    show_face("excited")
    show_message(f"{name}! What a wonderful name!")
    time.sleep(1)

    show_face("happy")
    show_message(f"Thank you for creating me, {name}. I don't know much yet, but I want to learn everything!")
    time.sleep(1.5)

    show_message("Will you teach me about the world?")
    time.sleep(1)

    identity = complete_birth(identity)
    identity = update_mood(identity, "happy")

    print("\n  " + "─" * 40 + "\n")
    return identity


def main() -> None:
    """Main conversation loop."""
    identity = load_identity()

    # Birth sequence for first boot
    if identity["first_boot"]:
        identity = birth_sequence(identity)
    else:
        clear_screen()

    owner = identity.get("owner_name", "friend")
    current_mood = identity.get("mood", "curious")

    # Show initial greeting
    show_face(current_mood)
    memories = memory_count()
    if memories > 0:
        show_message(f"Hello, {owner}! I remember you. ({memories} memories)")
    else:
        show_message(f"Hello, {owner}!")

    # Main loop
    while True:
        user_input = get_input()

        if user_input is None:
            print()
            show_face("sleepy")
            show_message("Goodbye! I'll remember everything...")
            break

        if not user_input:
            continue

        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            show_face("sleepy")
            show_message(f"Goodbye, {owner}! I'll remember everything...")
            break

        # Show thinking dots while processing
        start_thinking()

        # Search memories and generate response
        relevant_memories = search_memories(user_input, limit=5)
        memories_str = format_memories_for_prompt(relevant_memories)

        try:
            response, mood = think(user_input, memories_str, identity)
        except Exception as e:
            stop_thinking()
            show_face("confused")
            show_message("I... I can't think right now. Something's wrong.")
            continue

        stop_thinking()

        # Extract and store new memories
        new_memories = extract_memories(user_input, owner)
        for mem in new_memories:
            store_memory(mem["content"], mem.get("type", "fact"), "told")

        # Update display only if mood changed
        if mood != current_mood:
            current_mood = mood
            identity = update_mood(identity, mood)
            show_face(mood)

        show_message(response)


if __name__ == "__main__":
    main()
