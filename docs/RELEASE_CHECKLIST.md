# Release / Model Promotion Checklist

Do not promote a model or pipeline change to official league use until the applicable items are reviewed.

## Reproducibility
- [ ] Code commit recorded
- [ ] Model version recorded
- [ ] Dataset version and split recorded
- [ ] Training/inference configuration recorded
- [ ] Dependencies/environment recorded

## Evaluation
- [ ] Held-out games evaluated
- [ ] No test-set leakage
- [ ] Precision and recall reported
- [ ] Per-gym results reported
- [ ] Per-stat/event results reported
- [ ] Identity precision and coverage reported
- [ ] Review/unresolved rate reported
- [ ] False positives and false negatives inspected
- [ ] Comparison against current production baseline

## Operational readiness
- [ ] Full-game processing tested
- [ ] Retry/idempotency tested
- [ ] Failure handling tested
- [ ] Storage and security reviewed
- [ ] Cost per game measured
- [ ] Monitoring/logging available
- [ ] Rollback path documented

## Product owner approval
- [ ] Review workload acceptable
- [ ] Statistical integrity checks pass
- [ ] Official-use thresholds met
- [ ] Product owner explicitly approves rollout
