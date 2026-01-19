"""Main entry point for Pal - Personal Artificial Lifeform."""

import time

from face import clear_screen, draw_screen
from animator import get_animator
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

    # First consciousness - use static draws for birth (more controlled)
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

    draw_screen("happy", "What is your name?", show_input=True)
    try:
        name = input().strip()
    except (EOFError, KeyboardInterrupt):
        name = ""

    while not name:
        draw_screen("confused", "I... I didn't hear that. What's your name?", show_input=True)
        try:
            name = input().strip()
        except (EOFError, KeyboardInterrupt):
            name = ""

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
    """Main conversation loop with animated face."""
    # Load identity
    identity = load_identity()

    # Birth sequence for first boot (uses static display)
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

    # Start animator for main loop
    animator = get_animator()
    animator.start()
    animator.set_mood(identity["mood"], greeting, transition=False)

    # Main loop
    try:
        while True:
            user_input = animator.get_input()

            if user_input is None:  # Ctrl+C or EOF
                animator.set_mood("sleepy", "Goodbye! I'll remember everything...")
                time.sleep(2)
                break

            if not user_input:
                # Redraw current state
                animator.set_mood(identity["mood"], animator._message, transition=False)
                continue

            # Exit commands
            if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
                animator.set_mood("sleepy", f"Goodbye, {owner}! I'll remember everything...")
                time.sleep(2)
                break

            # Show thinking animation while processing
            animator.set_mood("thinking", "")
            animator.set_thinking(True)

            # Search for relevant memories
            relevant_memories = search_memories(user_input, limit=5)
            memories_str = format_memories_for_prompt(relevant_memories)

            # Generate response
            try:
                response, mood = think(user_input, memories_str, identity)
            except Exception as e:
                animator.set_thinking(False)
                animator.set_mood("confused", "I... I can't think right now. Something's wrong.")
                continue

            # Stop thinking animation
            animator.set_thinking(False)

            # Extract and store new memories from user's message
            new_memories = extract_memories(user_input, owner)
            for mem in new_memories:
                store_memory(mem["content"], mem.get("type", "fact"), "told")

            # Update mood and display response with transition
            identity = update_mood(identity, mood)
            animator.set_mood(mood, response, transition=True)

    finally:
        animator.stop()


if __name__ == "__main__":
    main()
