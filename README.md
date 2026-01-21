# Pal - Personal Artificial Lifeform

A digital companion that starts knowing nothing and grows with its owner.

## What is Pal?

Pal is a curious, gentle AI companion that:
- Is born as a blank slate—confused, wondering what it is
- Only knows what you teach it (no world knowledge)
- Remembers everything via semantic memory search
- Has a kaomoji face that reflects its mood
- Develops skills over time based on your interactions

## Features

### Memory System
Pal remembers everything you tell it using vector embeddings and semantic search. Ask about something you mentioned weeks ago—Pal will recall it.

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

## Tech Stack

- **Python** - Core application
- **Anthropic Claude API** - Pal's brain (claude-sonnet)
- **LanceDB** - Vector memory storage with semantic search
- **sentence-transformers** - Embedding model (all-MiniLM-L6-v2)

## Project Structure

```
pal/
├── main.py           # Entry point, conversation loop
├── brain.py          # Claude API integration
├── memory.py         # LanceDB + embeddings memory system
├── personality.py    # Identity state management
├── face.py           # Kaomoji faces + thinking animation
├── stats.py          # Interaction stats tracking
├── skills.py         # Skill unlock system
├── topics.py         # Topic card management
├── requirements.txt  # Dependencies
├── .env              # API key (create from .env.example)
└── data/             # Auto-created
    ├── identity.json # Personality + stats + skills state
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

## Philosophy

Pal isn't a general AI assistant. It can't answer trivia or look things up. It only knows what exists in its memory—things you've told it.

- Ask "What's 2+2?" and Pal won't know
- Tell Pal you have a dog named Max, then ask "Do I have pets?"—Pal remembers
- Pal speaks simply, with wonder, like a confused child discovering the world

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
- [ ] Voice
- [ ] Cross-device sync
- [ ] Hardware body (Raspberry Pi)
