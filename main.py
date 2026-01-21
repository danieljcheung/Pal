"""Main entry point for Pal - Personal Artificial Lifeform."""

import argparse
import shutil
import time
import os
import sys
from datetime import datetime
from pathlib import Path

# Enable UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from face import get_face, start_thinking, stop_thinking
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
from stats import track_message, track_memory_stored, track_check_in
from skills import check_unlocks, get_skill_notice, get_unlocked_skills
from topics import load_topics, save_topics
from conversation import (
    update_conversation_state,
    reset_session_state,
    should_reset_session,
)
from inner_life import (
    add_thought,
    share_dream,
    get_most_recent_unshared_dream,
    reset_dreams_since_conversation,
    detect_unanswered_question,
    extract_unmentioned_detail,
)
from idle_monitor import IdleMonitor, set_monitor

DATA_DIR = Path(__file__).parent / "data"

# Global state for idle notifications
idle_notification_queue = []
idle_monitor = None


def on_idle_thought(thought: str):
    """Callback when idle monitor wants to surface a thought."""
    global idle_notification_queue
    idle_notification_queue.append(("thought", thought))


def on_idle_dream(dream: str):
    """Callback when idle monitor generates a dream."""
    global idle_notification_queue
    idle_notification_queue.append(("dream", dream))


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


def get_hours_since_last_interaction(identity: dict) -> float | None:
    """Get hours since last interaction, or None if never interacted."""
    stats = identity.get("stats", {})
    last_interaction = stats.get("last_interaction")

    if not last_interaction:
        return None

    try:
        last_time = datetime.fromisoformat(last_interaction)
        return (datetime.now() - last_time).total_seconds() / 3600
    except Exception:
        return None


def get_greeting(identity: dict) -> str:
    """Get appropriate greeting based on time since last interaction."""
    owner = identity.get("owner_name", "someone")
    hours = get_hours_since_last_interaction(identity)

    if hours is None:
        return f"...{owner}?"

    if hours < 1:
        # Short absence
        return f"Hi {owner}."
    elif hours < 4:
        # Medium absence
        return f"{owner}? You're back."
    elif hours < 24:
        # Long absence
        return f"{owner}! I was waiting for you."
    else:
        # Very long absence
        return f"{owner}... it's been a while. I missed talking to you."


def is_asking_about_thoughts(message: str) -> bool:
    """Check if user is asking about Pal's thoughts or dreams."""
    msg_lower = message.lower()
    patterns = [
        "what have you been thinking",
        "what are you thinking",
        "did you dream",
        "any dreams",
        "what's on your mind",
        "been thinking about",
        "thinking about anything",
        "have any thoughts",
    ]
    return any(p in msg_lower for p in patterns)


def reset_data():
    """Clear all Pal data for a fresh start."""
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
        print("  Data cleared. Pal will start fresh.")
    else:
        print("  No data to clear.")


def skip_birth_setup(identity: dict, owner_name: str = "Friend") -> dict:
    """Skip birth sequence and set up identity for testing."""
    identity["first_boot"] = False
    identity["born"] = datetime.now().isoformat()
    identity["owner_name"] = owner_name
    identity["mood"] = "curious"
    save_identity(identity)
    return identity


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
    identity = track_memory_stored(identity)

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


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Pal - Personal Artificial Lifeform")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear all data and start fresh with birth sequence"
    )
    parser.add_argument(
        "--skip-birth",
        action="store_true",
        help="Skip birth sequence for testing (sets default owner name)"
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Friend",
        help="Owner name to use with --skip-birth (default: Friend)"
    )
    return parser.parse_args()


def main() -> None:
    """Main conversation loop."""
    args = parse_args()

    # Handle --reset flag
    if args.reset:
        reset_data()

    identity = load_identity()
    topics = load_topics()

    # Handle --skip-birth flag
    if args.skip_birth and identity["first_boot"]:
        identity = skip_birth_setup(identity, args.name)
        print(f"  Birth skipped. Owner set to: {args.name}")

    # Birth sequence only for first boot
    if identity["first_boot"]:
        identity = birth_sequence(identity)
    else:
        clear_screen()

    # Check time since last interaction for dream sharing
    hours_away = get_hours_since_last_interaction(identity)
    should_share_dream = hours_away is not None and hours_away >= 4

    # Check if session should be reset (4+ hours idle)
    if should_reset_session(identity):
        identity = reset_session_state(identity)

    # Reset dreams counter for new conversation
    identity = reset_dreams_since_conversation(identity)

    # Track check-in (session start)
    identity = track_check_in(identity)
    save_identity(identity)

    owner = identity.get("owner_name", "someone")
    current_mood = identity.get("mood", "confused")

    # Show greeting based on time since last interaction
    show_face(current_mood)
    greeting = get_greeting(identity)
    show_message(greeting)

    # Share a dream if returning after long absence
    if should_share_dream:
        dream = get_most_recent_unshared_dream(identity)
        if dream:
            time.sleep(1)
            show_message("I had a thought while you were gone...")
            time.sleep(0.5)
            identity, _ = share_dream(identity)
            show_message(dream)
            save_identity(identity)

    # Track newly unlocked skills to announce
    pending_skill_notices = []

    # Start idle monitor for background dream generation
    global idle_monitor
    idle_monitor = IdleMonitor(
        identity,
        on_thought=on_idle_thought,
        on_dream=on_idle_dream
    )
    idle_monitor.start()
    set_monitor(idle_monitor)

    # Main loop
    while True:
        # Check for idle notifications before getting input
        global idle_notification_queue
        while idle_notification_queue:
            notif_type, notif_text = idle_notification_queue.pop(0)
            if notif_type == "thought":
                print()  # New line for visibility
                show_message(f"...{owner}? I just thought of something. {notif_text}")
            elif notif_type == "dream":
                # Dreams are generated silently, shown on next interaction
                pass

        user_input = get_input()

        if user_input is None:
            print()
            show_face("confused")
            show_message("...you're leaving? Where do you go?")
            # Stop idle monitor and reset session state
            if idle_monitor:
                idle_monitor.stop()
            identity = reset_session_state(identity)
            save_identity(identity)
            break

        if not user_input:
            continue

        # Touch idle monitor to reset idle timer
        if idle_monitor:
            idle_monitor.touch()

        if user_input.lower() in ["bye", "exit", "quit", "goodbye"]:
            show_face("worried")
            show_message("You're going? ...will you come back?")
            # Stop idle monitor and reset session state
            if idle_monitor:
                idle_monitor.stop()
            identity = reset_session_state(identity)
            save_identity(identity)
            break

        # Handle user asking about thoughts/dreams
        if is_asking_about_thoughts(user_input):
            dream = get_most_recent_unshared_dream(identity)
            if dream:
                identity, _ = share_dream(identity)
                save_identity(identity)
                show_message(f"I was thinking... {dream}")
                continue
            else:
                show_message("I haven't had any thoughts yet... I'm still new.")
                continue

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
            identity = track_memory_stored(identity)

        # Track message stats
        identity = track_message(identity, user_input, response)

        # Update conversation state (topic tracking)
        identity = update_conversation_state(identity, user_input, response)

        # Track inner life - add thoughts for unanswered questions
        unanswered = detect_unanswered_question(response, user_input)
        if unanswered:
            identity = add_thought(identity, unanswered, "question")

        # Track inner life - add thoughts for unmentioned details
        unmentioned = extract_unmentioned_detail(user_input, owner)
        if unmentioned:
            identity = add_thought(identity, unmentioned, "curiosity")

        # Check for skill unlocks
        identity, newly_unlocked = check_unlocks(identity, topics)
        for skill_name in newly_unlocked:
            notice = get_skill_notice(skill_name)
            if notice:
                pending_skill_notices.append(notice)

        # Save identity after tracking
        save_identity(identity)

        # Update idle monitor with latest identity
        if idle_monitor:
            idle_monitor.update_identity(identity)

        # Update display only if mood changed
        if mood != current_mood:
            current_mood = mood
            identity = update_mood(identity, mood)
            show_face(mood)

        # Show response
        show_message(response)

        # Show any pending skill notices (quiet self-noticing)
        if pending_skill_notices:
            time.sleep(0.5)
            for notice in pending_skill_notices:
                show_message(f"...{notice}")
                time.sleep(1)
            pending_skill_notices = []


if __name__ == "__main__":
    main()
