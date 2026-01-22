"""FastAPI server to bridge Tauri GUI with Pal's Python backend."""

import re
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from personality import load_identity, save_identity, update_mood, get_age
from brain import think, think_stream, extract_memories
from memory import search_memories, store_memory, format_memories_for_prompt, memory_count, get_all_memories
from conversation import update_conversation_state, reset_session_state, should_reset_session, get_pending_question
from stats import track_message, track_memory_stored, track_check_in
from skills import check_unlocks
from topics import load_topics, add_unresolved_question, save_topics, create_topic
from inner_life import detect_unanswered_question
from research import research_url, research_search, research_text
from skills import is_skill_unlocked


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


def check_unanswered_question(identity: dict, user_message: str, topics: dict) -> dict:
    """
    Check if there's a pending question from Pal that went unanswered.
    If so, add it to the topic's unresolved questions.

    Returns the updated topics dict.
    """
    pending_question, pending_topic = get_pending_question(identity)

    if not pending_question:
        return topics

    # Check if the user's message actually answers the question
    unanswered = detect_unanswered_question(pending_question, user_message)

    if unanswered:
        # Question went unanswered - add to topic's unresolved list
        topic_name = pending_topic or "general"

        # Create topic if it doesn't exist
        if topic_name not in topics:
            topics = create_topic(topics, topic_name)

        topics = add_unresolved_question(topics, topic_name, pending_question)
        print(f"[DEBUG] Added unresolved question to '{topic_name}': {pending_question}")

    return topics


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
    memories: list


class ResearchUrlRequest(BaseModel):
    url: str


class ResearchSearchRequest(BaseModel):
    query: str


class ResearchTextRequest(BaseModel):
    text: str


class ResearchResponse(BaseModel):
    success: bool
    summary: str
    topic: str
    facts_stored: int
    questions: list[str]
    sources: list[str] = []
    error: str | None = None
    skill_locked: bool = False


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

    # Check if there's an unanswered question from the previous turn
    topics = load_topics()
    topics = check_unanswered_question(identity, user_message, topics)

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

    # Check for skill unlocks (topics already loaded and updated above)
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


def _clean_mood_tag(text: str) -> str:
    """Remove mood tag from text."""
    return re.sub(r"\s*\[mood:\w+\]\s*", "", text).strip()


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message to Pal and get a streaming response via SSE."""
    identity = get_identity()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check if there's an unanswered question from the previous turn
    topics = load_topics()
    topics = check_unanswered_question(identity, user_message, topics)

    # Search relevant memories
    memories = search_memories(user_message, limit=5)
    memories_str = format_memories_for_prompt(memories)

    def generate():
        nonlocal identity, topics
        full_response = ""
        buffer = ""  # Buffer to handle mood tags split across chunks

        # Stream chunks from Claude
        for chunk in think_stream(user_message, memories_str, identity):
            if isinstance(chunk, dict):
                # Final message with mood
                mood = chunk.get("mood", "confused")

                # Send any remaining buffered text (cleaned of mood tag)
                if buffer:
                    clean_buffer = _clean_mood_tag(buffer)
                    if clean_buffer:
                        yield f"data: {json.dumps({'type': 'chunk', 'text': clean_buffer})}\n\n"

                # Clean response of mood tag
                clean_response = _clean_mood_tag(full_response)

                # Update identity with mood and conversation state
                identity = update_mood(identity, mood)
                identity = update_conversation_state(identity, user_message, clean_response)
                identity = track_message(identity, user_message, clean_response)

                # Extract and store memories
                owner_name = identity.get("owner_name", "Friend")
                new_memories = extract_memories(user_message, owner_name)
                for mem in new_memories:
                    store_memory(mem["content"], mem.get("type", "fact"), "told")
                    identity = track_memory_stored(identity)

                # Check for skill unlocks (topics already loaded and updated above)
                identity, newly_unlocked = check_unlocks(identity, topics)
                save_and_update_identity(identity)

                skill_unlocked = newly_unlocked[0] if newly_unlocked else None

                # Send final event with metadata
                yield f"data: {json.dumps({'type': 'done', 'mood': mood, 'skill_unlocked': skill_unlocked})}\n\n"
            else:
                # Text chunk - accumulate full response
                full_response += chunk
                buffer += chunk

                # The mood tag [mood:xxx] is always at the end of the response
                # Strategy: hold back any text that could be the start of a mood tag

                # First, check if buffer contains a complete mood tag
                mood_match = re.search(r"\[mood:\w+\]", buffer)
                if mood_match:
                    # Complete mood tag found - send text before it, clear buffer
                    send_text = buffer[:mood_match.start()].rstrip()
                    buffer = ""
                    if send_text:
                        yield f"data: {json.dumps({'type': 'chunk', 'text': send_text})}\n\n"
                    continue

                # Look for potential partial mood tag at the end
                # Check for any of: [, [m, [mo, [moo, [mood, [mood:, [mood:x...
                bracket_pos = buffer.rfind('[')

                if bracket_pos == -1:
                    # No bracket, safe to send everything
                    send_text = buffer
                    buffer = ""
                else:
                    # Found bracket - check if it could be start of mood tag
                    potential_tag = buffer[bracket_pos:]
                    mood_prefix = "[mood:"

                    # Check if this could be the start of [mood:...]
                    is_potential_mood_tag = (
                        len(potential_tag) <= len(mood_prefix) and
                        mood_prefix.startswith(potential_tag)
                    ) or potential_tag.startswith(mood_prefix)

                    if is_potential_mood_tag:
                        # Hold back the potential tag
                        send_text = buffer[:bracket_pos]
                        buffer = potential_tag
                    else:
                        # Not a mood tag, safe to send
                        send_text = buffer
                        buffer = ""

                if send_text:
                    yield f"data: {json.dumps({'type': 'chunk', 'text': send_text})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/brain", response_model=BrainResponse)
async def get_brain():
    """Get Pal's brain data for visualization."""
    identity = get_identity()
    topics = load_topics()
    memories = get_all_memories()

    return BrainResponse(
        stats=identity.get("stats", {}),
        skills=identity.get("skills", {}),
        topics=topics,
        inner_life=identity.get("inner_life", {}),
        memory_count=memory_count(),
        memories=memories,
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


def _check_research_skill() -> tuple[bool, ResearchResponse | None]:
    """Check if research skill is unlocked. Returns (is_unlocked, error_response)."""
    identity = get_identity()
    if not is_skill_unlocked(identity, "research"):
        return False, ResearchResponse(
            success=False,
            summary="",
            topic="",
            facts_stored=0,
            questions=[],
            error="I don't know how to do that yet... maybe someday.",
            skill_locked=True,
        )
    return True, None


@app.post("/research/url", response_model=ResearchResponse)
async def research_url_endpoint(request: ResearchUrlRequest):
    """Research a URL - fetch, process, and learn from it."""
    # Check skill unlock
    unlocked, error_response = _check_research_skill()
    if not unlocked:
        return error_response

    result = research_url(request.url)

    return ResearchResponse(
        success=result["success"],
        summary=result["summary"],
        topic=result["topic"],
        facts_stored=result["facts_stored"],
        questions=result["questions"],
        error=result["error"],
    )


@app.post("/research/search", response_model=ResearchResponse)
async def research_search_endpoint(request: ResearchSearchRequest):
    """Research via web search - search, read, and learn."""
    # Check skill unlock
    unlocked, error_response = _check_research_skill()
    if not unlocked:
        return error_response

    result = research_search(request.query)

    return ResearchResponse(
        success=result["success"],
        summary=result["summary"],
        topic=result["topic"],
        facts_stored=result["facts_stored"],
        questions=result["questions"],
        sources=result.get("sources", []),
        error=result["error"],
    )


@app.post("/research/text", response_model=ResearchResponse)
async def research_text_endpoint(request: ResearchTextRequest):
    """Research provided text - process and learn from it."""
    # Check skill unlock
    unlocked, error_response = _check_research_skill()
    if not unlocked:
        return error_response

    result = research_text(request.text)

    return ResearchResponse(
        success=result["success"],
        summary=result["summary"],
        topic=result["topic"],
        facts_stored=result["facts_stored"],
        questions=result["questions"],
        error=result["error"],
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
