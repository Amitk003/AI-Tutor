"""Verification of the grounded chat flow.

Run with: python -m tests.mock_chat_check
No real API key needed. Uses a fake LLM chat and a temp database.
"""

import os
import tempfile
import unittest.mock as mock

from backend import config
from backend import db
from backend import rag
from backend.tutor import answer_question

SAMPLE_TEXT = (
    "A binary search tree keeps keys in sorted order. The left child holds a "
    "smaller key. The right child holds a larger key. Search takes O(log n) "
    "time on a balanced tree. Red black trees are a balanced variant."
)


def _fake_embed(texts):
    return [[float(len(t) % 10 + 1), 0.5, -0.25] for t in texts]


def _fake_chat(system, user):
    return "A binary search tree keeps keys sorted. [1]"


def main() -> None:
    tmp = tempfile.mkdtemp()
    config.DATA_DIR = tmp
    config.DB_PATH = os.path.join(tmp, "test.db")
    config.UPLOAD_DIR = os.path.join(tmp, "uploads")
    db._connection = None

    sample_path = os.path.join(tmp, "notes.md")
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)

    with mock.patch("backend.rag.llm.embed", side_effect=_fake_embed), mock.patch(
        "backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]
    ), mock.patch("backend.tutor.llm.chat", side_effect=_fake_chat):
        rag.ingest_file(sample_path, "notes.md")

        # Normal grounded answer.
        result = answer_question("what is a binary search tree", [])
        assert result["answer"], "expected a non-empty answer"
        assert "[1]" in result["answer"], "answer should cite the source"
        assert result["citations"], "expected citations"
        assert result["citations"][0]["filename"] == "notes.md"
        print("grounded answer ok:", result["answer"])

        # History is accepted without error.
        history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
        result2 = answer_question("explain more", history)
        assert result2["answer"]
        print("history handling ok")

        # No material path: clear data, then ask a question.
    with mock.patch("backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]):
        db.execute("DELETE FROM chunks")
        db.execute("DELETE FROM documents")
        empty = answer_question("anything", [])
        assert "upload" in empty["answer"].lower() or "matched" in empty["answer"].lower()
        print("no-material ok")

        # LLM down path: chat raises, falls back to material.
        db._connection = None
        with mock.patch("backend.rag.llm.embed", side_effect=_fake_embed), mock.patch(
            "backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]
        ):
            rag.ingest_file(sample_path, "notes.md")
        with mock.patch("backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]), mock.patch(
            "backend.tutor.llm.chat", side_effect=RuntimeError("down")
        ):
            fallback = answer_question("red black trees", [])
            assert "available" in fallback["answer"].lower()
            print("llm-down fallback ok")

    print("ALL CHAT MOCK CHECKS PASSED")


if __name__ == "__main__":
    main()