"""Debug script to check Pal's memory state."""

from memory import search_memories, memory_count
from personality import load_identity

def main():
    print("=" * 50)
    print("PAL DEBUG INFO")
    print("=" * 50)

    print("\n[IDENTITY]")
    identity = load_identity()
    for k, v in identity.items():
        print(f"  {k}: {v}")

    print(f"\n[MEMORIES] ({memory_count()} total)")
    memories = search_memories("", limit=20)
    if memories:
        for m in memories:
            print(f"  - {m['content']}")
    else:
        print("  (none)")

    print("\n[STATUS]")
    if identity.get("first_boot"):
        print("  Pal has NOT completed birth sequence yet")
    else:
        print("  Pal has completed birth sequence")
        print(f"  Owner: {identity.get('owner_name', 'unknown')}")
        print(f"  Born: {identity.get('born', 'unknown')}")

    print()

if __name__ == "__main__":
    main()
