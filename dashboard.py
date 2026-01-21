"""Brain visualization dashboard for Pal."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Enable UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich import box

from personality import load_identity, get_age
from topics import load_topics, UNDERSTANDING_LEVELS
from memory import memory_count, search_memories
from inner_life import get_inner_life, get_unsurfaced_thoughts, get_unshared_dreams
from skills import UNLOCK_CONDITIONS, SKILL_DESCRIPTIONS
from face import FACES

console = Console(force_terminal=True)

# Skill unlock thresholds for progress display
SKILL_THRESHOLDS = {
    "greet": ("check_ins", 10),
    "recall": ("memories_stored", 25),
    "remind": ("reminders_requested", 5),
    "time_sense": ("messages_exchanged", 50),
    "notice_patterns": ("memories_stored", 50),
    "hold_thoughts": ("thought_dumps", 20),
    "opinions": ("messages_exchanged", 100),
    "tasks": ("reminders_delivered", 5),
    "summarize": ("memories_stored", 100),
    "concern": ("emotional_shares", 10),
}


def get_time_ago(iso_time: str) -> str:
    """Convert ISO time to human-readable 'X ago' format."""
    if not iso_time:
        return "never"

    try:
        dt = datetime.fromisoformat(iso_time)
        delta = datetime.now() - dt

        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} min ago"
        else:
            return "just now"
    except Exception:
        return "unknown"


def format_date(iso_time: str) -> str:
    """Format ISO time as readable date."""
    if not iso_time:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(iso_time)
        return dt.strftime("%b %d, %Y")
    except Exception:
        return "Unknown"


def make_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Create a text-based progress bar."""
    if total == 0:
        return "░" * width

    filled = int((current / total) * width)
    filled = min(filled, width)
    empty = width - filled
    return "█" * filled + "░" * empty


def get_understanding_progress(level: str) -> tuple[int, int]:
    """Get progress values for understanding level."""
    levels = {"surface": 1, "basic": 2, "familiar": 3, "knowledgeable": 4}
    current = levels.get(level, 1)
    return current, 4


def show_header(identity: dict):
    """Display the header section."""
    owner = identity.get("owner_name", "Unknown")
    mood = identity.get("mood", "confused")
    born = identity.get("born")
    age = get_age(identity)
    face = FACES.get(mood, "(◕~◕)?")

    born_str = format_date(born) if born else "Not yet born"

    header = Text()
    header.append(f"  Born: {born_str} ({age})\n", style="dim")
    header.append(f"  Owner: ", style="dim")
    header.append(f"{owner}\n", style="cyan bold")
    header.append(f"  Mood: ", style="dim")
    header.append(f"{face} {mood}", style="green" if mood == "happy" else "yellow")

    console.print(Panel(header, title="[bold magenta]Pal's Brain[/bold magenta]", box=box.ROUNDED))


def show_stats(identity: dict):
    """Display stats section."""
    stats = identity.get("stats", {})

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(width=30)
    table.add_column(width=30)

    table.add_row(
        f"[cyan]Messages:[/cyan] {stats.get('messages_exchanged', 0)}",
        f"[cyan]Memories:[/cyan] {stats.get('memories_stored', 0)}"
    )
    table.add_row(
        f"[cyan]Check-ins:[/cyan] {stats.get('check_ins', 0)}",
        f"[cyan]Unique days:[/cyan] {len(stats.get('unique_days', []))}"
    )
    table.add_row(
        f"[cyan]Questions answered:[/cyan] {stats.get('questions_answered', 0)}",
        f"[cyan]Corrections:[/cyan] {stats.get('corrections', 0)}"
    )
    table.add_row(
        f"[cyan]Emotional shares:[/cyan] {stats.get('emotional_shares', 0)}",
        f"[cyan]Thought dumps:[/cyan] {stats.get('thought_dumps', 0)}"
    )

    console.print(Panel(table, title="[bold]Stats[/bold]", box=box.ROUNDED))


def show_skills(identity: dict):
    """Display skills section with progress."""
    skills = identity.get("skills", {})
    stats = identity.get("stats", {})

    lines = []

    for skill_name, skill_data in skills.items():
        unlocked = skill_data.get("unlocked", False)
        level = skill_data.get("level", 0)
        uses = skill_data.get("uses", 0)

        if unlocked:
            # Green checkmark for unlocked
            status = f"[green]✓ {skill_name}[/green] [dim](lvl {level}, {uses} uses)[/dim]"
        else:
            # Show progress toward unlock
            threshold_info = SKILL_THRESHOLDS.get(skill_name)
            if threshold_info:
                stat_name, threshold = threshold_info
                current = stats.get(stat_name, 0)
                progress = min(current, threshold)
                bar = make_progress_bar(progress, threshold, 6)

                if progress >= threshold * 0.8:
                    # Yellow for close to unlocking
                    status = f"[yellow]○ {skill_name}[/yellow] [dim]{bar} {progress}/{threshold}[/dim]"
                else:
                    # Gray for locked
                    status = f"[dim]○ {skill_name} {bar} {progress}/{threshold}[/dim]"
            else:
                status = f"[dim]○ {skill_name}[/dim]"

        lines.append(status)

    # Arrange in two columns
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(width=35)
    table.add_column(width=35)

    for i in range(0, len(lines), 2):
        col1 = lines[i] if i < len(lines) else ""
        col2 = lines[i + 1] if i + 1 < len(lines) else ""
        table.add_row(col1, col2)

    console.print(Panel(table, title="[bold]Skills[/bold]", box=box.ROUNDED))


def show_topics(topics: dict, detailed: bool = False):
    """Display topics section."""
    if not topics:
        console.print(Panel("[dim]No topics discussed yet.[/dim]", title="[bold]Topics[/bold]", box=box.ROUNDED))
        return

    lines = []

    # Sort by times discussed
    sorted_topics = sorted(
        topics.items(),
        key=lambda x: x[1].get("times_discussed", 0),
        reverse=True
    )

    for topic_name, topic_data in sorted_topics[:8]:  # Show top 8
        display_name = topic_data.get("display_name", topic_name)
        understanding = topic_data.get("understanding", "surface")
        unresolved = len(topic_data.get("unresolved", []))
        times = topic_data.get("times_discussed", 0)

        # Understanding progress bar
        level_num, max_level = get_understanding_progress(understanding)
        bar = make_progress_bar(level_num, max_level, 10)

        # Color based on understanding
        color = {
            "surface": "dim",
            "basic": "yellow",
            "familiar": "cyan",
            "knowledgeable": "green"
        }.get(understanding, "dim")

        unresolved_str = f"[red]({unresolved} unresolved)[/red]" if unresolved > 0 else "[dim](0 unresolved)[/dim]"

        line = f"[{color}]{display_name:<12}[/{color}] {bar} [{color}]{understanding:<13}[/{color}] {unresolved_str}"
        lines.append(line)

        if detailed and topic_data.get("unresolved"):
            for q in topic_data["unresolved"][:2]:
                lines.append(f"  [dim]? {q}[/dim]")

    content = "\n".join(lines) if lines else "[dim]No topics yet.[/dim]"
    console.print(Panel(content, title="[bold]Topics[/bold]", box=box.ROUNDED))


def show_inner_life(identity: dict, detailed: bool = False):
    """Display inner life section."""
    inner_life = get_inner_life(identity)
    thoughts = get_unsurfaced_thoughts(identity)
    dreams = get_unshared_dreams(identity)

    lines = []

    # Thoughts
    lines.append(f"[cyan]Pending thoughts:[/cyan] {len(thoughts)}")
    if thoughts:
        for t in thoughts[:3]:
            lines.append(f"  [dim]- \"{t['thought']}\"[/dim]")
        if len(thoughts) > 3:
            lines.append(f"  [dim]  ...and {len(thoughts) - 3} more[/dim]")

    lines.append("")

    # Dreams
    lines.append(f"[cyan]Unshared dreams:[/cyan] {len(dreams)}")
    if dreams:
        for d in dreams[:2]:
            lines.append(f"  [dim]- \"{d['dream']}\"[/dim]")
        if len(dreams) > 2:
            lines.append(f"  [dim]  ...and {len(dreams) - 2} more[/dim]")

    if detailed:
        all_dreams = inner_life.get("dream_journal", [])
        if all_dreams:
            lines.append("")
            lines.append(f"[cyan]Full dream journal:[/cyan] {len(all_dreams)} dreams")
            for d in all_dreams:
                shared = "[green]✓[/green]" if d.get("shared") else "[yellow]○[/yellow]"
                lines.append(f"  {shared} \"{d['dream']}\"")

    content = "\n".join(lines)
    console.print(Panel(content, title="[bold]Inner Life[/bold]", box=box.ROUNDED))


def show_session(identity: dict):
    """Display session info."""
    stats = identity.get("stats", {})
    last_interaction = stats.get("last_interaction")

    lines = []
    lines.append(f"[cyan]Last interaction:[/cyan] {get_time_ago(last_interaction)}")
    lines.append(f"[cyan]Total check-ins:[/cyan] {stats.get('check_ins', 0)}")
    lines.append(f"[cyan]First met:[/cyan] {format_date(stats.get('first_met'))}")

    content = "\n".join(lines)
    console.print(Panel(content, title="[bold]Session[/bold]", box=box.ROUNDED))


def show_memories(limit: int = 20):
    """Show all memories."""
    # Search with empty query to get recent memories
    memories = search_memories("", limit=limit)

    if not memories:
        console.print(Panel("[dim]No memories stored yet.[/dim]", title="[bold]Memories[/bold]", box=box.ROUNDED))
        return

    table = Table(title="Memories", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Content", style="cyan")
    table.add_column("Type", style="yellow", width=12)
    table.add_column("Source", style="dim", width=8)

    for i, mem in enumerate(memories, 1):
        table.add_row(
            str(i),
            mem.get("content", "")[:60] + ("..." if len(mem.get("content", "")) > 60 else ""),
            mem.get("type", "fact"),
            mem.get("source", "told")
        )

    console.print(table)
    console.print(f"\n[dim]Total memories: {memory_count()}[/dim]")


def show_full_dashboard():
    """Display the full dashboard."""
    identity = load_identity()
    topics = load_topics()

    console.clear()
    console.print()

    show_header(identity)
    show_stats(identity)
    show_skills(identity)
    show_topics(topics)
    show_inner_life(identity)
    show_session(identity)


def main():
    parser = argparse.ArgumentParser(description="Pal's Brain Visualization Dashboard")
    parser.add_argument("--memories", action="store_true", help="List all memories")
    parser.add_argument("--topics", action="store_true", help="Detailed topic view")
    parser.add_argument("--dreams", action="store_true", help="Full dream journal")
    parser.add_argument("--stats", action="store_true", help="Just stats")
    parser.add_argument("--skills", action="store_true", help="Just skills")

    args = parser.parse_args()

    identity = load_identity()
    topics = load_topics()

    if args.memories:
        console.print()
        show_memories(limit=50)
    elif args.topics:
        console.print()
        show_topics(topics, detailed=True)
    elif args.dreams:
        console.print()
        show_inner_life(identity, detailed=True)
    elif args.stats:
        console.print()
        show_header(identity)
        show_stats(identity)
    elif args.skills:
        console.print()
        show_skills(identity)
    else:
        show_full_dashboard()


if __name__ == "__main__":
    main()
