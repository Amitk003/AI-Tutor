"""
SuperMemo SM-2 Spaced Repetition Scheduler.
Computes review intervals, ease factor progression, and next review dates.
Persists review schedules to RevisionSchedule database table.
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.core.config import settings
from backend.core.events import RevisionScheduled, event_dispatcher
from backend.database.models.revision_schedule import RevisionSchedule


class SM2Scheduler:
    """SuperMemo SM-2 spaced repetition scheduler."""

    def __init__(self, min_ease_factor: float = settings.SM2_MIN_EASE_FACTOR):
        self.min_ease_factor = min_ease_factor

    def calculate_sm2(
        self,
        quality: int,  # Grade 0 to 5
        repetition_count: int,
        ease_factor: float,
        interval_days: int,
    ) -> Dict[str, Any]:
        """
        Calculates next repetition count, ease factor, and review interval using SM-2 algorithm.

        Args:
            quality: User review quality grade (0=complete blackout, 5=perfect recall).
            repetition_count: Current successful repetition count (n).
            ease_factor: Current Ease Factor (EF, default: 2.5).
            interval_days: Current interval in days (I).

        Returns:
            Dict containing new repetition_count, ease_factor, and interval_days.
        """
        q = max(0, min(5, quality))

        # 1. Update Ease Factor (EF)
        new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(self.min_ease_factor, new_ef)

        # 2. Update Repetition Count (n) & Interval (I)
        if q < 3:  # Incorrect / failed recall
            new_n = 0
            new_interval = 1
        else:      # Successful recall
            new_n = repetition_count + 1
            if new_n == 1:
                new_interval = 1
            elif new_n == 2:
                new_interval = 6
            else:
                new_interval = math.ceil(interval_days * new_ef)

        next_review_date = datetime.now(timezone.utc) + timedelta(days=new_interval)

        logger.info(
            "SM-2 schedule update: q={q} n={n}->{nn} EF={ef:.2f}->{nef:.2f} I={i}->{ni} days",
            q=q,
            n=repetition_count,
            nn=new_n,
            ef=ease_factor,
            nef=new_ef,
            i=interval_days,
            ni=new_interval,
        )

        return {
            "repetition_count": new_n,
            "ease_factor": round(new_ef, 4),
            "interval_days": new_interval,
            "next_review_date": next_review_date,
        }

    async def schedule_revision(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        concept_name: str,
        quality_grade: int = 4,
    ) -> Dict[str, Any]:
        """
        Schedules next revision item in PostgreSQL RevisionSchedule table.
        Emits RevisionScheduled domain event.
        """
        res = await session.execute(
            select(RevisionSchedule)
            .where(RevisionSchedule.user_id == user_id)
            .where(RevisionSchedule.concept_name == concept_name)
        )
        record = res.scalars().first()

        n = record.repetition_count if record else 0
        ef = record.ease_factor if record else settings.SM2_INITIAL_EASE_FACTOR
        i = record.interval_days if record else 1

        sm2_res = self.calculate_sm2(quality=quality_grade, repetition_count=n, ease_factor=ef, interval_days=i)

        if not record:
            record = RevisionSchedule(
                user_id=user_id,
                concept_name=concept_name,
                ease_factor=sm2_res["ease_factor"],
                repetition_count=sm2_res["repetition_count"],
                interval_days=sm2_res["interval_days"],
                due_date=sm2_res["next_review_date"],
            )
            session.add(record)
        else:
            record.ease_factor = sm2_res["ease_factor"]
            record.repetition_count = sm2_res["repetition_count"]
            record.interval_days = sm2_res["interval_days"]
            record.due_date = sm2_res["next_review_date"]

        await session.commit()

        # Emit RevisionScheduled domain event
        await event_dispatcher.emit(
            RevisionScheduled(
                user_id=user_id,
                concept_name=concept_name,
                next_review_date=sm2_res["next_review_date"].strftime("%Y-%m-%d"),
                interval_days=sm2_res["interval_days"],
            )
        )

        return {
            "concept_name": concept_name,
            "ease_factor": sm2_res["ease_factor"],
            "interval_days": sm2_res["interval_days"],
            "due_date": sm2_res["next_review_date"],
        }


# Global SM-2 scheduler instance
sm2_scheduler = SM2Scheduler()
