# Pal - Personal Artificial Lifeform

A digital companion that starts knowing nothing and grows with its owner.

## What is Pal?

Pal is a curious, gentle AI companion that:
- Is born as a blank slate
- Only knows what you teach it
- Remembers everything and builds a relationship over time
- Has a kaomoji face that reflects its mood
- Feels alive—like Dobby from Harry Potter or JARVIS from Iron Man

## Tech Stack

- Python
- Ollama (local LLM) - Pal's brain
- LanceDB - Memory storage with semantic search
- sentence-transformers - Embedding model for memory retrieval

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Pull the LLM model
ollama pull phi3

# Run Pal
python main.py
```

## Philosophy

Pal isn't a general AI assistant. It can't answer trivia or look things up. It only knows what exists in its memory—things you've told it or things it has learned through tasks you've given it.

Every Pal is unique, shaped entirely by its owner.

## Status

Early development. Currently:
- [x] Memory system
- [x] Identity/personality state
- [x] Birth sequence
- [x] Conversation loop
- [x] Persistent kaomoji face
- [ ] Voice
- [ ] Cross-device sync
- [ ] Hardware body (Raspberry Pi)
