"""Verification of quiz generation and evaluation.

Run with: python -m tests.mock_quiz_check
No real API key needed. Uses a fake chat model and a temp database.
"""

import json
import os
import tempfile
import unittest.mock as mock

from backend import config
from backend import db
from backend import quiz
from backend import rag
from backend.quiz import QuizSchemaError

SAMPLE_TEXT = (
    "A binary search tree keeps keys in sorted order. The left child holds a "
    "smaller key. The right child holds a larger key. Search takes O(log n) "
    "time on a balanced tree. Red black trees are a balanced variant."
)

GOOD_JSON = json.dumps(
    {
        "questions": [
            {
                "question": "Which property holds in a binary search tree?",
                "options": [
                    "Left child is smaller",
                    "Left child is larger",
                    "All keys are equal",
                    "Right child is smaller",
                ],
                "correct_index": 0,
                "explanation": "The left child holds a smaller key.",
            }
        ]
    }
)


def _fake_embed(texts):
    return [[float(len(t) % 10 + 1), 0.5, -0.25] for t in texts]


def _fake_chat_ok(system, user):
    return GOOD_JSON


def _fake_chat_bad_json(system, user):
    return "not json at all"


def main() -> None:
    tmp = tempfile.mkdtemp()
    config.DATA_DIR = tmp
    config.DB_PATH = os.path.join(tmp, "test.db")
    config.UPLOAD_DIR = os.path.join(tmp, "uploads")
    db._connection = None

    sample_path = os.path.join(tmp, "notes.md")
    with open(sample_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)

    embed_patch = (
        mock.patch("backend.rag.llm.embed", side_effect=_fake_embed),
        mock.patch("backend.rag.llm.embed_one", side_effect=lambda t: _fake_embed([t])[0]),
    )
    for p in embed_patch:
        p.start()

    rag.ingest_file(sample_path, "notes.md")

    # Good JSON path.
    with mock.patch("backend.quiz.llm.chat", side_effect=_fake_chat_ok):
        questions = quiz.generate_quiz("binary search tree", count=1)
        assert len(questions) == 1
        q = questions[0]
        assert len(q["options"]) == 4
        assert q["correct_index"] == 0
        assert q["question"]
        assert q["explanation"]
        print("good json path ok:", q["question"])

        # Evaluate correct and wrong answers.
        res = quiz.evaluate(0, 0, q["explanation"])
        assert res["correct"] is True
        res2 = quiz.evaluate(2, 0, q["explanation"])
        assert res2["correct"] is False
        print("evaluate ok")

        # JSON wrapped in markdown fences must still parse.
        fenced = f"```json\n{GOOD_JSON}\n```"
        parsed = quiz._parse_questions(fenced)
        assert len(parsed) == 1
        print("fenced json ok")

    # Bad JSON path: retries exhaust and QuizSchemaError is raised.
    with mock.patch("backend.quiz.llm.chat", side_effect=_fake_chat_bad_json):
        try:
            quiz.generate_quiz("binary search tree", count=1, max_retries=2)
            raise AssertionError("expected QuizSchemaError")
        except QuizSchemaError:
            print("bad json retry path ok")

    # No material path.
    db.execute("DELETE FROM chunks")
    db.execute("DELETE FROM documents")
    with mock.patch("backend.quiz.llm.chat", side_effect=_fake_chat_ok):
        try:
            quiz.generate_quiz("anything", count=1)
            raise AssertionError("expected QuizSchemaError for no material")
        except QuizSchemaError:
            print("no-material path ok")

    for p in embed_patch:
        p.stop()

    print("ALL QUIZ MOCK CHECKS PASSED")


if __name__ == "__main__":
    main()