"""Memory system for Pal using LanceDB and sentence-transformers."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import lancedb
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).parent / "data"
MEMORIES_DIR = DATA_DIR / "memories"

# Global instances (lazy loaded)
_db = None
_table = None
_model = None


def _get_model() -> SentenceTransformer:
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_db():
    """Lazy load the LanceDB connection."""
    global _db
    if _db is None:
        DATA_DIR.mkdir(exist_ok=True)
        MEMORIES_DIR.mkdir(exist_ok=True)
        _db = lancedb.connect(str(MEMORIES_DIR))
    return _db


def _get_table():
    """Get or create the memories table."""
    global _table
    if _table is None:
        db = _get_db()
        try:
            _table = db.open_table("memories")
        except Exception:
            # Table doesn't exist, create it with a dummy record then delete it
            model = _get_model()
            dummy_vector = model.encode("initialization").tolist()
            db.create_table(
                "memories",
                [
                    {
                        "id": "init",
                        "content": "init",
                        "type": "system",
                        "source": "system",
                        "timestamp": datetime.now().isoformat(),
                        "vector": dummy_vector,
                    }
                ],
            )
            _table = db.open_table("memories")
            # Delete the init record
            _table.delete('id = "init"')
    return _table


def store_memory(
    content: str,
    memory_type: str = "fact",
    source: str = "told",
) -> str:
    """
    Store a new memory with its embedding.

    Args:
        content: The memory text to store
        memory_type: Type of memory (fact, preference, about_owner)
        source: How the memory was acquired (told, learned)

    Returns:
        The ID of the stored memory
    """
    model = _get_model()
    table = _get_table()

    memory_id = str(uuid.uuid4())
    vector = model.encode(content).tolist()

    table.add(
        [
            {
                "id": memory_id,
                "content": content,
                "type": memory_type,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "vector": vector,
            }
        ]
    )

    return memory_id


def search_memories(query: str, limit: int = 5) -> list[dict]:
    """
    Search memories using semantic similarity.

    Args:
        query: The search query
        limit: Maximum number of results

    Returns:
        List of matching memories
    """
    table = _get_table()

    # Check if table has any records
    if table.count_rows() == 0:
        return []

    model = _get_model()
    query_vector = model.encode(query).tolist()

    results = table.search(query_vector).limit(limit).to_list()

    # Clean up results
    memories = []
    for r in results:
        memories.append(
            {
                "id": r["id"],
                "content": r["content"],
                "type": r["type"],
                "source": r["source"],
                "timestamp": r["timestamp"],
                "distance": r.get("_distance", None),  # Include similarity score for debugging
            }
        )

    # Debug: log what was found
    if memories:
        print(f"[DEBUG] Memory search for '{query[:50]}...' found {len(memories)} results:")
        for m in memories[:3]:
            print(f"  - {m['content'][:60]}... (type={m['type']}, dist={m.get('distance', '?')})")

    return memories


def get_all_memories() -> list[dict]:
    """Get all stored memories sorted by timestamp (newest first)."""
    table = _get_table()

    row_count = table.count_rows()
    if row_count == 0:
        return []

    # Get all records using PyArrow
    arrow_table = table.to_arrow()

    # Convert to list of dicts
    memories = []
    for i in range(arrow_table.num_rows):
        memories.append({
            "id": str(arrow_table["id"][i]),
            "content": str(arrow_table["content"][i]),
            "type": str(arrow_table["type"][i]),
            "source": str(arrow_table["source"][i]),
            "timestamp": str(arrow_table["timestamp"][i]),
        })

    # Sort by timestamp descending (newest first)
    memories.sort(key=lambda m: m["timestamp"], reverse=True)

    return memories


def memory_count() -> int:
    """Get the number of stored memories."""
    table = _get_table()
    return table.count_rows()


def format_memories_for_prompt(memories: list[dict]) -> str:
    """Format memories as a string for the LLM prompt."""
    if not memories:
        return "I don't have any memories yet. I'm completely new to this world."

    lines = []
    for m in memories:
        lines.append(f"- {m['content']}")

    return "\n".join(lines)
