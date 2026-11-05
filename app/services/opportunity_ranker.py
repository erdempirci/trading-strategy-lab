"""Evidence-gated, deterministic opportunity ranking."""
from dataclasses import dataclass
from datetime import datetime, timezone

from app.strategies.base import SignalCandidate


@dataclass(frozen=True)
class RankedCandidate:
    candidate: SignalCandidate
    score: float
    eligible: bool
    rejection_reasons: tuple[str, ...]


def rank_candidates(candidates: list[SignalCandidate], *, now: datetime | None = None,
                    minimum_oos_trades: int = 30, minimum_score: float = 60.0) -> list[RankedCandidate]:
    """Rank validated candidates. Missing evidence makes a candidate ineligible.

    Score weights: OOS evidence 30, regime fit 20, net expectancy 20,
    cost efficiency 10, signal quality 10, diversification metadata 10.
    The score is a prioritization index, not a probability of profit.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    ranked = []
    for item in candidates:
        reasons = []
        if not item.data_quality_valid:
            reasons.append("invalid_or_unverified_data")
        if not item.validation_id or item.out_of_sample_trades < minimum_oos_trades:
            reasons.append("insufficient_out_of_sample_evidence")
        if item.out_of_sample_expectancy_r is None or item.out_of_sample_expectancy_r <= 0:
            reasons.append("non_positive_or_missing_expectancy")
        if item.expires_at <= current:
            reasons.append("expired_candidate")
        if item.estimated_cost_r >= 1:
            reasons.append("estimated_cost_exceeds_one_r")

        expectancy = max(0.0, min(1.0, (item.out_of_sample_expectancy_r or 0.0) / 0.5))
        evidence = min(1.0, item.out_of_sample_trades / 100.0)
        cost_efficiency = max(0.0, 1.0 - item.estimated_cost_r)
        diversification = 1.0 if len(set(item.currency_exposures)) <= 2 else 0.5
        score = 30 * evidence + 20 * item.regime_fit + 20 * expectancy + \
            10 * cost_efficiency + 10 * item.signal_quality + 10 * diversification
        eligible = not reasons and score >= minimum_score
        if not reasons and score < minimum_score:
            reasons.append("score_below_minimum")
        ranked.append(RankedCandidate(item, round(score, 4), eligible, tuple(reasons)))
    return sorted(ranked, key=lambda x: (x.eligible, x.score), reverse=True)


def select_best_candidate(candidates: list[SignalCandidate], **kwargs) -> RankedCandidate | None:
    ranked = rank_candidates(candidates, **kwargs)
    return next((item for item in ranked if item.eligible), None)
