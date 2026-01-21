"""FastAPI server to bridge Tauri GUI with Pal's Python backend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from personality import load_identity, save_identity, update_mood, get_age
from brain import think, extract_memories
from memory import search_memories, store_memory, format_memories_for_prompt, memory_count, get_all_memories
from conversation import update_conversation_state, reset_session_state, should_reset_session
from stats import track_message, track_memory_stored, track_check_in
from skills import check_unlocks
from topics import load_topics


# Global identity state
_identity = None


def get_identity():
    """Get the current identity, loading if necessary."""
    global _identity
    if _identity is None:
        _identity = load_identity()
    return _identity


def save_and_update_identity(identity):
    """Save identity and update global state."""
    global _identity
    save_identity(identity)
    _identity = identity


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load identity on startup."""
    global _identity
    _identity = load_identity()

    # Track check-in
    _identity = track_check_in(_identity)

    # Reset session if idle for 4+ hours
    if should_reset_session(_identity):
        _identity = reset_session_state(_identity)

    save_identity(_identity)
    yield


app = FastAPI(title="Pal API", lifespan=lifespan)

# Allow CORS for Tauri app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tauri uses tauri://localhost or http://localhost
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    mood: str
    skill_unlocked: str | None = None


class IdentityResponse(BaseModel):
    name: str
    owner_name: str | None
    mood: str
    born: str | None
    age: str
    first_boot: bool


class BrainResponse(BaseModel):
    stats: dict
    skills: dict
    topics: dict
    inner_life: dict
    memory_count: int


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "name": "Pal API"}


@app.get("/identity", response_model=IdentityResponse)
async def get_identity_endpoint():
    """Get Pal's current identity state."""
    identity = get_identity()

    return IdentityResponse(
        name=identity.get("name", "Pal"),
        owner_name=identity.get("owner_name"),
        mood=identity.get("mood", "curious"),
        born=identity.get("born"),
        age=get_age(identity),
        first_boot=identity.get("first_boot", True),
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to Pal and get a response."""
    identity = get_identity()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Search relevant memories
    memories = search_memories(user_message, limit=5)
    memories_str = format_memories_for_prompt(memories)

    # Get Pal's response
    response, mood = think(user_message, memories_str, identity)

    # Update mood
    identity = update_mood(identity, mood)

    # Update conversation state
    identity = update_conversation_state(identity, user_message, response)

    # Track message stats
    identity = track_message(identity, user_message, response)

    # Extract and store memories from user's message
    owner_name = identity.get("owner_name", "Friend")
    new_memories = extract_memories(user_message, owner_name)
    for mem in new_memories:
        store_memory(mem["content"], mem.get("type", "fact"), "told")
        identity = track_memory_stored(identity)

    # Check for skill unlocks
    topics = load_topics()
    identity, newly_unlocked = check_unlocks(identity, topics)

    # Save identity
    save_and_update_identity(identity)

    # Return first unlocked skill if any
    skill_unlocked = newly_unlocked[0] if newly_unlocked else None

    return ChatResponse(
        response=response,
        mood=mood,
        skill_unlocked=skill_unlocked,
    )


@app.get("/brain", response_model=BrainResponse)
async def get_brain():
    """Get Pal's brain data for visualization."""
    identity = get_identity()
    topics = load_topics()

    return BrainResponse(
        stats=identity.get("stats", {}),
        skills=identity.get("skills", {}),
        topics=topics,
        inner_life=identity.get("inner_life", {}),
        memory_count=memory_count(),
    )


@app.get("/history")
async def get_history():
    """Get conversation history (memories)."""
    memories = get_all_memories()
    return {"memories": memories}


@app.post("/reset-session")
async def reset_session():
    """Reset the conversation session state."""
    identity = get_identity()
    identity = reset_session_state(identity)
    save_and_update_identity(identity)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
