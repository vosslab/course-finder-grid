# Roadmap

This roadmap records only forward work supported by current repository evidence.
Completed scheduler and Mail-helper work remains in [CHANGELOG.md](CHANGELOG.md).

## Decisions before changes

- **Highest priority: atomic baseline persistence.** Decide whether all per-subject cache
  snapshots and durable full-section memory need one transactional, recoverable commit.
  The current update path copies snapshots sequentially and then saves memory, so an
  interruption can leave a mixed baseline. [CHANGELOG.md](CHANGELOG.md) identifies this
  as a separate architecture decision; [csv_cache.py](../course_scheduling/csv_cache.py)
  and [report_pipeline.py](../course_scheduling/report_pipeline.py) show the current order.
- **Follow-up: report-log repository root.** Decide whether report logging should derive the
  repository root from `git rev-parse` or retain its source-relative bootstrap path.
  The source-relative implementation avoids making failure logging depend on Git, but
  differs from the repository convention. The tradeoff remains unresolved in
  [CHANGELOG.md](CHANGELOG.md) and is implemented in
  [report_logging.py](../course_scheduling/report_logging.py).

## Human decision

- **Retire the legacy flat scripts.** The completed parity report finds the rewritten
  `course_scheduling` package safe to replace the old external flat-script tree, but
  leaves retirement to the human owner. Review and authorize that removal before anyone
  changes the legacy tree; it is outside this repository's tracked files. See
  [course_scheduling_rewrite_trust_report.md](active_plans/reports/course_scheduling_rewrite_trust_report.md).
