from typing import Dict, Any
from decimal import Decimal

from targets.selectors.target_selectors import get_indicator_current_value


def calculate_target_progress(goal) -> Dict[str, Any]:
    """Compute progress for a TargetGoal using DataSubmission values.

    Formula for decrease direction:
      progress = (baseline - current) / (baseline - target)

    For increase direction, invert numerator/denom accordingly.
    Returns percent (0-100) and status (on_track|at_risk|achieved).
    """
    current = get_indicator_current_value(goal.indicator, goal.organization)
    if current is None:
        return {'progress_percent': 0, 'status': 'pending', 'current_value': None}

    baseline = Decimal(str(goal.baseline_value))
    target = Decimal(str(goal.target_value))
    current_d = Decimal(str(current))

    # guard against identical baseline/target
    if baseline == target:
        pct = 100 if current_d == target else 0
    else:
        if goal.direction == goal.Direction.DECREASE:
            denom = baseline - target
            num = baseline - current_d
        else:
            denom = target - baseline
            num = current_d - baseline
        try:
            pct = int((num / denom) * 100) if denom != 0 else 0
        except Exception:
            pct = 0

    # clamp
    pct = max(0, min(100, int(pct)))

    # determine status
    if pct >= 100:
        status = 'achieved'
    elif pct >= 70:
        status = 'on_track'
    else:
        status = 'at_risk'

    return {'progress_percent': pct, 'status': status, 'current_value': float(current_d)}
