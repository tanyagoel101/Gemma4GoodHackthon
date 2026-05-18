from datetime import datetime, timedelta
from types import SimpleNamespace

from backend.services.insights import generate_session_insights
from backend.services.trends import compute_baseline_deviation_map, weighted_longitudinal_risk
from backend.utils import average_scores, build_baseline_scores, calculate_trend_direction


def make_session(**overrides):
    data = {
        "ttr_score": 0.6,
        "mlu_score": 14.0,
        "filler_density": 4.0,
        "idea_density": 0.6,
        "referential_cohesion": 0.25,
        "semantic_coherence": 8.1,
        "composite_risk_score": 28.0,
        "recorded_at": datetime.utcnow(),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_average_scores_and_baseline_shape():
    sessions = [make_session(composite_risk_score=30), make_session(composite_risk_score=40)]
    averages = average_scores(sessions)
    baseline = build_baseline_scores(sessions)
    assert averages["composite_risk_score"] == 35.0
    assert baseline.composite_risk_score == 35.0


def test_trend_direction_thresholds():
    assert calculate_trend_direction(60, 50) == "declining"
    assert calculate_trend_direction(40, 50) == "improving"
    assert calculate_trend_direction(51, 50) == "stable"


def test_composite_risk_score_clamps_and_rewards_healthy_scores():
    baseline = make_session()
    high_risk_session = make_session(
        ttr_score=0.3,
        mlu_score=6,
        filler_density=12,
        idea_density=0.2,
        referential_cohesion=0.8,
        semantic_coherence=4.5,
    )
    low_risk_session = make_session(
        ttr_score=0.65,
        mlu_score=16,
        filler_density=2,
        idea_density=0.7,
        referential_cohesion=0.18,
        semantic_coherence=9.0,
    )
    high_risk = weighted_longitudinal_risk(
        high_risk_session,
        [high_risk_session, make_session(ttr_score=0.32, filler_density=11.5)],
        baseline,
        compute_baseline_deviation_map(high_risk_session, baseline),
    )
    low_risk = weighted_longitudinal_risk(
        low_risk_session,
        [low_risk_session, make_session(ttr_score=0.63, filler_density=2.3)],
        baseline,
        compute_baseline_deviation_map(low_risk_session, baseline),
    )
    assert high_risk > low_risk
    assert 0 <= low_risk <= 100
    assert 0 <= high_risk <= 100


def test_generate_session_insights_uses_supportive_language():
    baseline = make_session()
    current = make_session(ttr_score=0.45, filler_density=7.5, semantic_coherence=7.1)
    insights = generate_session_insights(current, baseline, [current, make_session(ttr_score=0.47, filler_density=7.0)])
    assert insights["caregiver_summary"]
    assert "baseline" in insights["clinician_summary"].lower()
    assert insights["confidence"] in {"low", "moderate", "high"}
