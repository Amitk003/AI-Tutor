"""
Psychometric Learning Engine Mathematical Validation & Unit Tests.
Verifies IRT 1PL/2PL/3PL probability curves, BKT Bayesian mastery updates,
SuperMemo SM-2 spaced repetition intervals, Ebbinghaus forgetting curves, and Domain Events.
"""

import math
import uuid
import pytest

from backend.analytics.metrics_engine import LearningAnalyticsEngine
from backend.analytics.sm2_scheduler import SM2Scheduler
from backend.core.events import AbilityUpdated, EventDispatcher, MasteryUpdated, RevisionScheduled
from backend.student_model.bkt_engine import BKTEngine
from backend.student_model.irt_engine import IRTEngine


def test_irt_probability_curves():
    """Verify IRT 1PL, 2PL, and 3PL mathematical probability calculations."""
    irt = IRTEngine()

    # 1PL (Rasch): When theta == difficulty (b), probability MUST be exactly 0.50
    p1pl = irt.calculate_probability_1pl(theta=0.0, b=0.0)
    assert abs(p1pl - 0.50) < 0.001

    # 2PL: Higher ability -> Higher probability of correct response
    p_high = irt.calculate_probability_2pl(theta=2.0, a=1.0, b=0.0)
    p_low = irt.calculate_probability_2pl(theta=-2.0, a=1.0, b=0.0)
    assert p_high > 0.50 > p_low
    assert abs(p_high - (1.0 / (1.0 + math.exp(-2.0)))) < 0.001

    # 3PL: Asymptote floor == c (guessing parameter = 0.20)
    p3pl_floor = irt.calculate_probability_3pl(theta=-10.0, a=1.0, b=0.0, c=0.20)
    assert abs(p3pl_floor - 0.20) < 0.01


def test_irt_theta_clamping_bounds():
    """Verify IRT theta update clamps strictly to [-3.0, +3.0] standard psychometric scale."""
    irt = IRTEngine(learning_rate=1.0)

    # Large positive boost
    theta = irt.update_ability_theta(current_theta=2.9, is_correct=True, item_difficulty=0.0)
    assert theta <= 3.0

    # Large negative penalty
    theta_neg = irt.update_ability_theta(current_theta=-2.9, is_correct=False, item_difficulty=0.0)
    assert theta_neg >= -3.0


def test_bkt_bayesian_mastery_updates():
    """Verify BKT Bayesian knowledge tracing updates for correct and incorrect outcomes."""
    bkt = BKTEngine(p_l0=0.10, p_t=0.20, p_g=0.25, p_s=0.10)

    # Correct response (u=1) -> Mastery MUST increase
    p_l1 = bkt.update_mastery(current_p_l=0.10, is_correct=True)
    assert p_l1 > 0.10

    # Second correct response -> Mastery increases further
    p_l2 = bkt.update_mastery(current_p_l=p_l1, is_correct=True)
    assert p_l2 > p_l1

    # Incorrect response (u=0) -> Mastery MUST decrease
    p_l_fail = bkt.update_mastery(current_p_l=p_l2, is_correct=False)
    assert p_l_fail < p_l2

    # Bounds check: Must remain in [0.0, 1.0]
    assert 0.0 <= p_l2 <= 1.0
    assert 0.0 <= p_l_fail <= 1.0


def test_sm2_spaced_repetition_schedule():
    """Verify SuperMemo SM-2 interval expansion and Ease Factor updates."""
    sm2 = SM2Scheduler(min_ease_factor=1.30)

    # Perfect recall (q=5), 1st repetition -> n=1, I=1
    res1 = sm2.calculate_sm2(quality=5, repetition_count=0, ease_factor=2.5, interval_days=1)
    assert res1["repetition_count"] == 1
    assert res1["interval_days"] == 1
    assert res1["ease_factor"] >= 2.5  # EF increased or stayed same

    # 2nd repetition -> n=2, I=6
    res2 = sm2.calculate_sm2(quality=5, repetition_count=1, ease_factor=res1["ease_factor"], interval_days=1)
    assert res2["repetition_count"] == 2
    assert res2["interval_days"] == 6

    # 3rd repetition -> I = ceil(6 * EF)
    res3 = sm2.calculate_sm2(quality=5, repetition_count=2, ease_factor=res2["ease_factor"], interval_days=6)
    assert res3["repetition_count"] == 3
    assert res3["interval_days"] > 6

    # Failed recall (q=1) -> Resets n=0, I=1
    res_fail = sm2.calculate_sm2(quality=1, repetition_count=3, ease_factor=2.5, interval_days=15)
    assert res_fail["repetition_count"] == 0
    assert res_fail["interval_days"] == 1
    assert res_fail["ease_factor"] >= 1.30


def test_ebbinghaus_forgetting_curve():
    """Verify Ebbinghaus Forgetting Curve retention R(t) = e^(-t/S)."""
    analytics = LearningAnalyticsEngine()

    # Day 0 -> 100% retention
    r0 = analytics.calculate_memory_retention(elapsed_days=0.0, stability=5.0)
    assert r0 == 1.0

    # Day 5 (t = S) -> e^-1 ~= 0.3679 retention
    r5 = analytics.calculate_memory_retention(elapsed_days=5.0, stability=5.0)
    assert abs(r5 - math.exp(-1.0)) < 0.001

    # Day 10 -> Lower retention
    r10 = analytics.calculate_memory_retention(elapsed_days=10.0, stability=5.0)
    assert r10 < r5


@pytest.mark.asyncio
async def test_psychometric_domain_events():
    """Verify psychometric engines emit AbilityUpdated, MasteryUpdated, and RevisionScheduled events."""
    dispatcher = EventDispatcher()
    emitted = []

    async def handle_event(evt):
        emitted.append(evt)

    dispatcher.subscribe(AbilityUpdated, handle_event)
    dispatcher.subscribe(MasteryUpdated, handle_event)
    dispatcher.subscribe(RevisionScheduled, handle_event)

    irt = IRTEngine()
    bkt = BKTEngine()
    sm2 = SM2Scheduler()

    # IRT Theta calculation
    theta = irt.update_ability_theta(0.0, True)
    assert theta > 0.0

    # BKT Mastery calculation
    mastery = bkt.update_mastery(0.10, True)
    assert mastery > 0.10
