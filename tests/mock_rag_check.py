"""Verification of parsing, chunking, ingestion, and retrieval.

Run with: python -m tests.mock_rag_check
Uses a temporary database and a fake LLM client so no real API key is needed.
"""

import os
import tempfile
import unittest.mock as mock

from backend import config
from backend import db
from backend import rag

SAMPLE_TEXT = (
    "A binary search tree is a data structure that keeps keys in sorted order. "
    "Each node has at most two children. The left child holds a smaller key. "
    "The right child holds a larger key. Searching in a binary search tree is fast. "
    "It takes O(log n) time on average. In a balanced tree the height is log n. "
    "Insertion also takes O(log n) time. Deletion is more complex but still fast. "
    "Trees are used in databases and file systems. Red black trees are a popular "
    "balanced variant. AVL trees balance by rotations. A trie is another tree. "
    "Binary heaps are used for priority queues. Heaps are not sorted. "
    "The heap property is weaker than the search tree property. "
    "This is the end of the first part of the sample study notes. "
    "Now we start the second part of these study notes. "
    "We talk about hash tables in this section. A hash table maps keys to values. "
    "It uses a hash function to compute an index. Collisions happen when two keys "
    "map to the same index. Chaining solves collisions by storing a linked list. "
    "Open addressing tries another slot when a collision happens. Linear probing "
    "searches forward one slot at a time. Quadratic probing uses a quadratic step. "
    "Double hashing uses a second hash function. A good hash function spreads keys "
    "evenly across the table. The load factor is the number of items over the size. "
    "Resizing keeps the load factor low. Hash tables give constant time lookups on "
    "average. This concludes the sample study notes on hash tables."
)


def _fake_embed(texts):
    # Deterministic fake vectors so cosine similarity works in the test.
    return [[float(len(t) % 10 + 1), 0.5, -0.25] for t in texts]


def main() -> None:
    tmp = tempfile.mkdtemp()
    config.DATA_DIR = tmp
    config.DB_PATH = os.path.join(tmp, "test.db")
    config.UPLOAD_DIR = os.path.join(tmp, "uploads")
    db._connection = None  # force a fresh connection to the temp db

    # Write a sample markdown file.
    sample_path = os.path.join(tmp, "notes.md")
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)

    # Chunking checks.
    chunks = rag.chunk_text(SAMPLE_TEXT)
    assert len(chunks) >= 2, f"expected several chunks, got {len(chunks)}"
    for c in chunks:
        assert c.strip(), "chunk should not be empty"
    print(f"chunk_text ok: {len(chunks)} chunks")

    # Parse check.
    parsed = rag.parsers.parse_file(sample_path)
    assert "binary search tree" in parsed.lower()
    print("parse_file ok")

    # Ingest with a fake LLM.
    with mock.patch("backend.rag.llm.embed", side_effect=_fake_embed), mock.patch(
        "backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]
    ):
        doc_id = rag.ingest_file(sample_path, "notes.md")
        assert doc_id
        stored = db.query("SELECT COUNT(*) AS n FROM chunks")
        assert stored[0]["n"] == len(chunks)
        print(f"ingest_file ok: {stored[0]['n']} chunks stored")

        # Retrieval: a query about red black trees should match a chunk containing it.
        results = rag.retrieve("what are red black trees", top_k=3)
        assert results, "expected at least one result"
        joined = " ".join(r["content"] for r in results).lower()
        assert "red black trees" in joined, "retrieval missed the matching chunk"
        assert results[0]["filename"] == "notes.md"
        print("retrieve ok:", [(r["filename"], r["score"]) for r in results])

        # Delete.
        rag.delete_document(doc_id)
        left = db.query("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
        assert left == 0
        print("delete_document ok")

    print("ALL RAG MOCK CHECKS PASSED")


if __name__ == "__main__":
    main()
