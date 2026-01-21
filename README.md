# Pal - Personal Artificial Lifeform

A digital companion that starts knowing nothing and grows with its owner.

## What is Pal?

Pal is a curious, gentle AI companion that:
- Is born as a blank slate—confused, wondering what it is
- Only knows what you teach it (no world knowledge)
- Remembers everything via semantic memory search
- Has a kaomoji face that reflects its mood
- Develops skills over time based on your interactions
- Has an inner life—thoughts and dreams even when you're away
- Feels alive—like Dobby from Harry Potter or JARVIS from Iron Man

## Features

### Memory System
Pal remembers everything you tell it using vector embeddings and semantic search. Ask about something you mentioned weeks ago—Pal will recall it.

### Inner Life
Pal has a mind that keeps working even when you're not there:

**Thought Queue**
- Unanswered questions get stored for later
- Curiosities about things you mention (girlfriend, pet, job)
- Pal can bring these up naturally in conversation

**Dream Journal**
- Reflections generated during idle time
- Connections between memories
- Shared when you return after long absence

```
Pal: dan! I was waiting for you.
Pal: I had a thought while you were gone...
Pal: I wondered if code could feel things.
```

Ask "what have you been thinking about?" to hear Pal's dreams.

### Conversation Tracking
Pal tracks what you're discussing and stays on topic:
- Current topic maintained until resolved
- No jumping back to old topics after "yes/no"
- Questions already asked are tracked (no repeats)
- Handles short responses gracefully

### Skill System
Pal develops abilities through interaction:

| Skill | Unlocks When |
|-------|--------------|
| greet | 10 check-ins |
| recall | 25 memories stored |
| remind | 5 reminder requests |
| time_sense | 50 messages + 3 unique days |
| notice_patterns | 50 memories + 10 emotional shares |
| hold_thoughts | 20 thought dumps |
| opinions | 100 messages + 10 corrections |
| research | 3 topics with unresolved questions |
| tasks | 5 reminders delivered |
| summarize | 100 memories stored |
| concern | 10 emotional shares |

When a skill unlocks, Pal quietly notices: *"...Hm. I remembered that without you asking. That's new."*

### Stats Tracking
Every interaction is tracked:
- Messages exchanged
- Memories stored
- Emotional shares
- Questions asked/answered
- Corrections received
- Reminders requested/delivered
- Thought dumps
- Check-ins
- Unique days interacted

### Topic Cards
Pal tracks understanding of topics you discuss:
- **surface** → **basic** → **familiar** → **knowledgeable**
- Topics level up based on discussions and memories linked to them

### Time-Based Greetings
Pal's greeting changes based on how long you've been away:

| Time Away | Greeting |
|-----------|----------|
| < 1 hour | "Hi dan." |
| 1-4 hours | "dan? You're back." |
| 4-24 hours | "dan! I was waiting for you." |
| 24+ hours | "dan... it's been a while. I missed talking to you." |

## Tech Stack

- **Python** - Core application
- **Anthropic Claude API** - Pal's brain (claude-sonnet)
- **LanceDB** - Vector memory storage with semantic search
- **sentence-transformers** - Embedding model (all-MiniLM-L6-v2)

## Project Structure

```
pal/
├── main.py           # Entry point, conversation loop
├── brain.py          # Claude API integration + system prompt
├── memory.py         # LanceDB + embeddings memory system
├── personality.py    # Identity state management
├── face.py           # Kaomoji faces + thinking animation
├── stats.py          # Interaction stats tracking
├── skills.py         # Skill unlock system
├── topics.py         # Topic card management
├── conversation.py   # Topic tracking + conversation state
├── inner_life.py     # Thought queue + dream journal
├── requirements.txt  # Dependencies
├── .env              # API key (create from .env.example)
└── data/             # Auto-created
    ├── identity.json # Personality + stats + skills + inner life
    ├── topics.json   # Topic cards
    └── memories/     # LanceDB storage
```

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run Pal
python main.py
```

On first run, Pal will go through a birth sequence—confused, wondering what it is, asking who you are.

### Command Line Flags

```bash
python main.py              # Normal start
python main.py --reset      # Clear all data, start fresh
python main.py --skip-birth # Skip birth sequence (for testing)
python main.py --skip-birth --name Dan  # Skip birth, set owner name
python main.py --help       # Show all options
```

## Philosophy

Pal isn't a general AI assistant. It can't answer trivia or look things up. It only knows what exists in its memory—things you've told it.

- Ask "What's 2+2?" and Pal won't know
- Tell Pal you have a dog named Max, then ask "Do I have pets?"—Pal remembers
- Pal speaks simply, with wonder, like a confused child discovering the world
- Say "yes" to confirm, "no" to correct—Pal understands short responses
- Pal stays on topic and doesn't repeat questions

Every Pal is unique, shaped entirely by its owner.

## Kaomoji Faces

```
(◕‿◕)   happy
(◕ᴗ◕)?  curious
(◕▽◕)!  excited
(◕_◕)   thinking
(◕~◕)?  confused
(◕︵◕)  sad
(◕︿◕)  worried
(◡‿◡)   sleepy
```

## Status

Early development. Currently:
- [x] Memory system with semantic search
- [x] Identity/personality state
- [x] Birth sequence
- [x] Conversation loop
- [x] Persistent kaomoji face
- [x] Stats tracking
- [x] Skill unlock system
- [x] Topic cards
- [x] Conversation tracking (topic continuity)
- [x] Inner life (thought queue + dream journal)
- [x] Time-based greetings
- [x] Command line flags
- [ ] Background dream generation (idle)
- [ ] Voice
- [ ] Cross-device sync
- [ ] Hardware body (Raspberry Pi)
