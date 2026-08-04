"""Verification of SM-2 spaced repetition and revision scheduling.

Run with: python -m tests.mock_revision_check
Uses a temporary database.
"""

import os
import tempfile

from datetime import date, timedelta

from backend import config
from backend import db
from backend import revision


def main() -> None:
    tmp = tempfile.mkdtemp()
    config.DATA_DIR = tmp
    config.DB_PATH = os.path.join(tmp, "test.db")
    db._connection = None

    today = date.today()

    # First schedule: due tomorrow.
    card = revision.schedule("binary search tree")
    assert card["interval_days"] == 1
    assert card["next_review"] == (today + timedelta(days=1)).isoformat()
    assert card["ease"] == 2.5
    print("schedule ok:", card["next_review"])

    # Nothing due today yet.
    assert revision.get_due_revisions() == []
    print("due-empty ok")

    # Grade 4 (success) on first review.
    g1 = revision.grade("binary search tree", 4)
    assert g1["repetitions"] == 1
    assert g1["interval_days"] == 1  # after first success, interval is 1
    assert g1["next_review"] == (today + timedelta(days=1)).isoformat()
    print("grade success #1 ok")

    # Grade 4 again: second success gives interval 6.
    g2 = revision.grade("binary search tree", 4)
    assert g2["repetitions"] == 2
    assert g2["interval_days"] == 6
    g3 = revision.grade("binary search tree", 5)
    # Third success uses old ease: interval = round(6 * 2.5) = 15.
    assert g3["interval_days"] == 15, g3
    assert g3["ease"] == 2.6  # ease updated after computing the interval
    print("grade success interval progression ok:", g1["interval_days"], g2["interval_days"], g3["interval_days"])

    # Failure resets repetitions and answer resulting interval.
    gf = revision.grade("binary search tree", 1)
    assert gf["repetitions"] == 0
    assert gf["interval_days"] == 1
    print("grade failure reset ok")

    # Invalid quality raises.
    try:
        revision.grade("binary search tree", 7)
        raise AssertionError("expected ValueError for bad quality")
    except ValueError:
        print("invalid quality ok")

    # Grading a topic with no card creates one (treated as failure).
    newg = revision.grade("hash tables", 3)
    assert newg["interval_days"] >= 1
    print("auto-create on grade ok")

    # Due list: make a card overdue and confirm it shows.
    db.execute(
        "UPDATE revisions SET next_review = ? WHERE topic = ?",
        ((today - timedelta(days=1)).isoformat(), "hash tables"),
    )
    due = revision.get_due_revisions()
    topics = [r["topic"] for r in due]
    assert "hash tables" in topics
    print("due-revisions ok:", topics)

    print("ALL REVISION MOCK CHECKS PASSED")


if __name__ == "__main__":
    main()