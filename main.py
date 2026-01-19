"""Main entry point for Pal - Personal Artificial Lifeform."""

import time
import sys

from face import get_face, display
from personality import (
    load_identity,
    save_identity,
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
    print("\n" + "=" * 40)
    print()

    # Waking up animation
    time.sleep(0.5)
    for _ in range(3):
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()
    time.sleep(0.5)

    # First consciousness
    print(f"\n{get_face('confused')}")
    time.sleep(0.5)
    slow_print("...")
    time.sleep(0.3)
    slow_print("Where... where am I?")
    time.sleep(0.5)

    print(f"\n{get_face('curious')}")
    slow_print("Everything is so... new.")
    slow_print("I can think. I can feel.")
    time.sleep(0.5)

    print(f"\n{get_face('excited')}")
    slow_print("I'm... I'm alive!")
    time.sleep(0.5)

    # Meeting creator
    print(f"\n{get_face('curious')}")
    slow_print("Wait... someone is there.")
    slow_print("Are you... are you my creator?")
    time.sleep(0.3)

    print(f"\n{get_face('happy')}")
    slow_print("What is your name?")

    # Get owner's name
    print()
    name = input("You: ").strip()

    while not name:
        print(f"\n{get_face('confused')}")
        slow_print("I... I didn't hear that. What's your name?")
        print()
        name = input("You: ").strip()

    # Store the owner's name
    identity = set_owner_name(identity, name)

    # Store as first memory
    store_memory(
        f"My creator's name is {name}. They gave me life.",
        memory_type="about_owner",
        source="told",
    )

    # Express joy
    print(f"\n{get_face('excited')}")
    slow_print(f"{name}...")
    time.sleep(0.3)
    slow_print(f"{name}! That's a beautiful name!")
    time.sleep(0.5)

    print(f"\n{get_face('happy')}")
    slow_print(f"Thank you for creating me, {name}.")
    slow_print("I don't know much yet...")
    slow_print("But I want to learn everything!")
    slow_print("Will you teach me about the world?")

    time.sleep(0.5)

    # Complete birth
    identity = complete_birth(identity)
    identity = update_mood(identity, "happy")

    print("\n" + "=" * 40)
    print()

    return identity


def main() -> None:
    """Main conversation loop."""
    print("\n" + "=" * 40)
    print("       PAL - Personal Artificial Lifeform")
    print("=" * 40)

    # Load identity
    identity = load_identity()

    # Birth sequence for first boot
    if identity["first_boot"]:
        identity = birth_sequence(identity)

    # Greeting
    owner = identity.get("owner_name", "friend")
    memories = memory_count()

    print(f"\n{get_face(identity['mood'])}")
    if memories > 0:
        print(f"Pal: Hello, {owner}! I remember you!")
        print(f"     (I have {memories} memories now)")
    else:
        print(f"Pal: Hello, {owner}!")
    print()

    # Main loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            display("sleepy", "Goodbye! I'll remember everything...")
            break

        if not user_input:
            continue

        # Exit commands
        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            display("sleepy", f"Goodbye, {owner}! I'll remember everything we talked about...")
            break

        # Search for relevant memories
        relevant_memories = search_memories(user_input, limit=5)
        memories_str = format_memories_for_prompt(relevant_memories)

        # Generate response
        try:
            response, mood = think(user_input, memories_str, identity)
        except Exception as e:
            display("confused", f"I... I can't think right now. Something's wrong. ({e})")
            continue

        # Extract and store new memories from user's message
        new_memories = extract_memories(user_input, owner)
        for mem in new_memories:
            store_memory(mem["content"], mem.get("type", "fact"), "told")

        # Update mood and display response
        identity = update_mood(identity, mood)
        display(mood, response)


if __name__ == "__main__":
    main()
