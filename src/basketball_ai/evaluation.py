"""Score predicted events against labelled ground truth (docs/DATASET_AND_EVALUATION.md §6).

Events match when the type agrees and their times are within `tolerance_seconds`; each truth event matches at
most one prediction (greedy by time distance). Reports precision, recall and F1 per event type, plus team and
player attribution accuracy on matched pairs. Never just one overall accuracy number (PROJECT_PLAN §8).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from basketball_ai.contracts import Event


@dataclass(frozen=True)
class TypeScore:
    eventType: str
    truePositives: int
    falsePositives: int
    falseNegatives: int

    @property
    def precision(self) -> float:
        n = self.truePositives + self.falsePositives
        return self.truePositives / n if n else 0.0

    @property
    def recall(self) -> float:
        n = self.truePositives + self.falseNegatives
        return self.truePositives / n if n else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if p + r else 0.0


@dataclass(frozen=True)
class EvaluationReport:
    byType: dict[str, TypeScore]
    matched: int
    teamCorrect: int
    playerAttributed: int  # matched pairs where the prediction named a player
    playerCorrect: int
    unattributedPredictions: int  # matched predictions with playerId null (allowed, not wrong)

    @property
    def team_accuracy(self) -> float:
        return self.teamCorrect / self.matched if self.matched else 0.0

    @property
    def player_precision(self) -> float:
        """Of the players the model credited, how many were right (the number that must be high)."""
        return self.playerCorrect / self.playerAttributed if self.playerAttributed else 0.0


def evaluate(
    predicted: Sequence[Event], truth: Sequence[Event], tolerance_seconds: float = 1.0
) -> EvaluationReport:
    preds = [e for e in predicted if e.status not in ("rejected",)]
    by_type_pred: dict[str, list[Event]] = defaultdict(list)
    by_type_true: dict[str, list[Event]] = defaultdict(list)
    for e in preds:
        by_type_pred[e.eventType].append(e)
    for e in truth:
        by_type_true[e.eventType].append(e)
    scores: dict[str, TypeScore] = {}
    pairs: list[tuple[Event, Event]] = []
    for etype in sorted(set(by_type_pred) | set(by_type_true)):
        candidates = sorted(
            (abs(p.timestampSeconds - t.timestampSeconds), i, j)
            for i, p in enumerate(by_type_pred[etype])
            for j, t in enumerate(by_type_true[etype])
            if abs(p.timestampSeconds - t.timestampSeconds) <= tolerance_seconds
        )
        used_p: set[int] = set()
        used_t: set[int] = set()
        for _, i, j in candidates:
            if i in used_p or j in used_t:
                continue
            used_p.add(i)
            used_t.add(j)
            pairs.append((by_type_pred[etype][i], by_type_true[etype][j]))
        tp = len(used_p)
        scores[etype] = TypeScore(etype, tp, len(by_type_pred[etype]) - tp, len(by_type_true[etype]) - tp)
    attributed = [(p, t) for p, t in pairs if p.playerId is not None]
    return EvaluationReport(
        byType=scores,
        matched=len(pairs),
        teamCorrect=sum(p.teamId == t.teamId for p, t in pairs),
        playerAttributed=len(attributed),
        playerCorrect=sum(p.playerId == t.playerId for p, t in attributed),
        unattributedPredictions=len(pairs) - len(attributed),
    )
