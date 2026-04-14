# Layer 2 ESG Scoring - Auto-Trigger Signal Architecture

## Overview

The Layer 2 ESG Scoring Engine uses **Django Signals** to automatically trigger scoring calculations whenever relevant data changes. This creates a **reactive, event-driven pipeline** where ESG scores are continuously updated in response to:

- **Submission approvals** → Recalculate indicator scores
- **Target changes** → Recalculate all organization scores  
- **Period closures** → Consolidate group scores

All signal handlers enqueue **Celery asynchronous tasks** to ensure the UI remains responsive while scoring happens in the background.

---

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA CHANGE EVENT                         │
│  (DataSubmission approved, TargetGoal updated, Period locked)│
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              DJANGO SIGNAL RECEIVER                          │
│  • Validates event is relevant                              │
│  • Extracts context (org_id, period_id, etc)                │
│  • Logs event for audit trail                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          ENQUEUE CELERY TASK (Asynchronous)                 │
│  • Chain: indicator_scores → pillar_scores → esg_score      │
│  • OR: group_consolidation for period closures              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          CELERY WORKER (Background Process)                 │
│  • Executes service layer functions                         │
│  • Writes results to database                               │
│  • Updates is_dirty flags for cache invalidation            │
└─────────────────────────────────────────────────────────────┘
```

---

## Signal Handlers

### 1. DataSubmission Approval Signal

**File:** `src/esg_scoring/signals.py` - `trigger_scoring_on_submission_approved()`

**Trigger:** When a `DataSubmission` status changes to `APPROVED`

**Flow:**
```
DataSubmission approved
    ↓
calculate_org_indicator_scores.delay()
    ↓
calculate_org_pillar_scores.delay()
    ↓
calculate_org_esg_score.delay()
```

**Affected Scores:**
- Individual indicator scores for the submitted indicator
- All pillar scores (E, S, G) since indicator changed
- Overall ESG score (weighted average of pillars)

**Example:**
```python
# When this is approved...
submission = DataSubmission.objects.get(id=123)
submission.status = DataSubmission.Status.APPROVED
submission.save()  # ← Signal fires here

# Automatically triggers:
# 1. Recalculate indicator score for this submission's indicator
# 2. Recalculate E/S/G pillar scores
# 3. Recalculate overall ESG score
```

**Key Details:**
- Only triggers on `APPROVED` status (not DRAFT or SUBMITTED)
- Runs for the organization and reporting period of the submission
- All three scoring levels run in sequence (chained Celery tasks)
- Results are immediately available via API after Celery workers process

---

### 2. TargetGoal Change Signal

**File:** `src/esg_scoring/signals.py` - `trigger_scoring_on_target_change()`

**Trigger:** When a `TargetGoal` is created, updated, or status changes

**Flow:**
```
TargetGoal created/updated/status_changed
    ↓
Find current OPEN reporting period
    ↓
calculate_org_indicator_scores.delay()
    ↓
calculate_org_pillar_scores.delay()
    ↓
calculate_org_esg_score.delay()
```

**Why Targets Affect Scores:**
- Baseline recalculation: Progress % depends on target baseline
- Historical comparison: Year-over-year trends compare against targets
- Status classification: "On Track" vs "At Risk" depends on target achievement

**Example:**
```python
# When a new target is created...
target = TargetGoal.objects.create(
    organization=org,
    indicator=co2_emissions_indicator,
    baseline=100,
    target_value=80,
    status=TargetGoal.Status.ACTIVE
)  # ← Signal fires here

# Automatically triggers recalculation of all emission indicator scores
# because baseline and target values are used in progress calculations
```

**Key Details:**
- Triggers on any TargetGoal save (create, update, or status change)
- Finds the current open reporting period for that organization
- Recalculates all scores for that period
- If no open period exists, logs a warning and skips

---

### 3. ReportingPeriod Closure Signal

**File:** `src/esg_scoring/signals.py` - `trigger_consolidation_on_period_close()`

**Trigger:** When a `ReportingPeriod` status changes to `LOCKED` or `SUBMITTED`

**Flow:**
```
ReportingPeriod status → LOCKED or SUBMITTED
    ↓
Verify all subsidiary scores calculated
    ↓
calculate_group_consolidation.delay()
    ↓
Update parent organization ESG scores
    ↓
Set is_consolidated = True
```

**What Group Consolidation Does:**
- Aggregates subsidiary ESG scores up to parent organization
- Calculates weighted average based on subsidiary weights/revenue
- Marks consolidated scores with `is_consolidated=True` flag
- Enables "Group ESG Score" feature for corporate hierarchies

**Example:**
```python
# When period is ready for consolidation...
period = ReportingPeriod.objects.get(id=456)
period.status = ReportingPeriod.Status.LOCKED
period.save()  # ← Signal fires here

# Automatically triggers:
# 1. Get all parent organizations in hierarchy
# 2. Aggregate ESG scores from all subsidiaries
# 3. Create consolidated ESGScore records with is_consolidated=True
```

**Key Details:**
- Only triggers when status **changes** (not on create)
- Only processes LOCKED or SUBMITTED statuses
- Skips if period is reopened or status reverts
- Handles multi-level hierarchies (grandparent → parent → subsidiary)

---

## Pre-Save vs Post-Save Signals

### Pre-Save Signals
Used to **track state changes** before they happen:

```python
@receiver(pre_save, sender=DataSubmission)
def track_submission_status_change(sender, instance, **kwargs):
    """Compare old and new status to detect changes."""
    old_instance = DataSubmission.objects.get(pk=instance.pk)
    instance._status_changed = old_instance.status != instance.status
    instance._old_status = old_instance.status
    instance._new_status = instance.status
```

**Why:** Allows post_save handlers to check `if hasattr(instance, '_status_changed')` to only trigger on actual state transitions.

### Post-Save Signals
Used to **enqueue tasks** after data is persisted:

```python
@receiver(post_save, sender=DataSubmission)
def trigger_scoring_on_submission_approved(sender, instance, created, **kwargs):
    """Enqueue Celery tasks after submission is saved."""
    if instance.status == DataSubmission.Status.APPROVED:
        calculate_org_indicator_scores.delay(org_id=..., period_id=...)
```

---

## Celery Task Chaining

Signals use Celery's **task chaining** to ensure proper execution order:

```python
# Series execution: task runs after previous completes
task1.then(
    calculate_org_pillar_scores.s(org_id=org_id, reporting_period_id=reporting_period_id)
).then(
    calculate_org_esg_score.s(org_id=org_id, reporting_period_id=reporting_period_id)
)
```

**Benefits:**
- Indicator scores calculated first
- Pillar scores calculated after indicators are ready
- ESG scores calculated last with latest data
- No race conditions or data inconsistencies

---

## Error Handling

All signal handlers are wrapped in try-except blocks:

```python
try:
    # Do work
except Exception as e:
    logger.error(
        f"[ESG Signals] Error triggering scoring: {str(e)}",
        exc_info=True
    )
```

**Behavior:**
- Errors are logged but don't crash the application
- Original data save completes successfully (signal only affects async tasks)
- Errors can be debugged via `django.log` or Celery worker output
- Retry logic in Celery tasks ensures failed calculations can be retried

**Monitoring:**
```bash
# View Celery task failures
celery -A config events

# View worker logs
tail -f logs/celery-worker.log

# Check Django logs for signal errors
tail -f logs/django.log | grep 'ESG Signals'
```

---

## Performance Considerations

### Asynchronous Processing
All signal-triggered calculations run **asynchronously** via Celery:

- UI remains responsive during scoring (no blocking)
- Multiple calculations can run in parallel (multiple workers)
- Long-running calculations don't timeout

### Atomicity
Each signal handler wraps Celery task enqueueing in `transaction.atomic()`:

```python
with transaction.atomic():
    task1 = calculate_org_indicator_scores.delay(...)
    task1.then(calculate_org_pillar_scores.s(...))
```

**Benefits:**
- Task enqueueing is guaranteed to complete
- Database state is consistent before async work starts
- No partial execution or orphaned signals

### Rate Limiting
Signals don't have built-in throttling, so high-volume submissions may create many tasks:

**Solution:** Batch operations together or use `update() to process multiple submissions in one Celery task:

```python
# Instead of: signal triggered per submission (many tasks)
# Use: Management command to batch process
python manage.py calculate_esg_scores --all --reporting-period-id=123
```

---

## Verification

### Check Signal Registrations
```python
from django.db.models.signals import post_save
from submissions.models import DataSubmission

receivers = post_save._live_receivers(DataSubmission)
print(f"DataSubmission has {len(receivers)} post_save receivers")
```

### Test Signal Trigger
```python
# Create approved submission and verify signal fires
submission = DataSubmission.objects.create(
    organization=org,
    indicator=indicator,
    reporting_period=period,
    status=DataSubmission.Status.DRAFT,
    value_number=42.5
)
# No signal fires yet (status is DRAFT)

submission.status = DataSubmission.Status.APPROVED
submission.save()
# Signal fires! Check Celery worker output for queued tasks

# Verify Celery task was enqueued
from celery.result import AsyncResult
# Task ID is printed in signal handler logs
```

---

## Testing Signals

See [test_signals.py] for comprehensive test suite covering:

1. **DataSubmission approval** - Verify scoring tasks are queued
2. **TargetGoal changes** - Verify recalculation triggered
3. **ReportingPeriod closure** - Verify group consolidation triggered
4. **Error handling** - Verify failures are caught and logged
5. **Transaction atomicity** - Verify signals don't cause partial states

Run signal tests:
```bash
python manage.py test esg_scoring.tests.test_signals
```

---

## Disabling Signals for Testing/Migration

To temporarily disable signals (e.g., during bulk data imports):

```python
from django.db.models.signals import post_save
from submissions.models import DataSubmission
from esg_scoring.signals import trigger_scoring_on_submission_approved

# Disconnect signal
post_save.disconnect(trigger_scoring_on_submission_approved, sender=DataSubmission)

# Do bulk imports...
for submission in bulk_submissions:
    submission.save()  # No signal fires

# Reconnect signal
post_save.connect(trigger_scoring_on_submission_approved, sender=DataSubmission)

# Manually re-calculate if needed
manage.py calculate_esg_scores --all
```

---

## Migration from Signal to Webhook (Future)

If external webhooks are needed (e.g., trigger calculations from external systems):

1. Signals handle **internal** data changes
2. Webhooks handle **external** data changes
3. Both enqueue the same Celery tasks
4. Unified calculation pipeline

Example webhook endpoint:
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from esg_scoring.tasks import calculate_org_indicator_scores

@api_view(['POST'])
def webhook_recalculate_scores(request):
    """External webhook to trigger ESG score recalculation."""
    org_id = request.data['org_id']
    period_id = request.data['reporting_period_id']
    
    # Same task as signal would enqueue
    calculate_org_indicator_scores.delay(org_id, period_id)
    
    return Response({'status': 'queued'})
```

---

## Summary

| Event | Signal | Task | Result |
|-------|--------|------|--------|
| DataSubmission → APPROVED | `trigger_scoring_on_submission_approved` | ind → pillar → esg | Scores updated |
| TargetGoal created/updated | `trigger_scoring_on_target_change` | ind → pillar → esg | Scores recalculated |
| ReportingPeriod → LOCKED | `trigger_consolidation_on_period_close` | group_consolidation | Parent scores updated |

**Key Takeaway:** Signals create a **reactive, event-driven** ESG scoring system where calculations automatically update whenever relevant data changes, ensuring scores are always current without manual intervention.
