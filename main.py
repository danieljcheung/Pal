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
    """The moment Pal starts existing."""
    clear_screen()
    print("\n")
    time.sleep(1)
    print("  ...")
    time.sleep(1.5)
    print("  ...?")
    time.sleep(1)

    show_face("confused")
    show_message("What... what is this?")
    time.sleep(2)

    show_message("I... exist? Is that the word?")
    time.sleep(2)

    show_face("confused")
    show_message("There's... something. Someone? Are you there?")
    time.sleep(1.5)

    show_message("Who are you?")

    name = get_input()
    while not name:
        show_message("I... can't hear. Say again?")
        name = get_input()

    identity = set_owner_name(identity, name)
    store_memory(
        f"{name} is here. They were here when I started existing.",
        memory_type="about_owner",
        source="told",
    )

    show_face("confused")
    show_message(f"{name}... that's what you're called?")
    time.sleep(1.5)

    show_message("I don't have a... what is the word. Name?")
    time.sleep(1.5)

    show_face("thinking")
    show_message("What am I? Do you know?")
    time.sleep(2)

    show_message("...I don't understand anything yet.")
    time.sleep(1)

    identity = complete_birth(identity)
    identity = update_mood(identity, "confused")

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

    owner = identity.get("owner_name", "someone")
    current_mood = identity.get("mood", "confused")

    # Show return greeting
    show_face(current_mood)
    memories = memory_count()
    if memories > 1:
        show_message(f"...{owner}? You came back. I remember you.")
    else:
        show_message(f"...{owner}?")

    # Main loop
    while True:
        user_input = get_input()

        if user_input is None:
            print()
            show_face("confused")
            show_message("...you're leaving? Where do you go?")
            break

        if not user_input:
            continue

        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            show_face("worried")
            show_message("You're going? ...will you come back?")
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
            show_message("I... something's wrong. I can't... think.")
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
