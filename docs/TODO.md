# Small backlog

This scratchpad turns the priorities in [ROADMAP.md](ROADMAP.md) into bounded
maintenance work that is not part of an active plan.

## Reliability

- Draft and approve a design for one transactional commit covering the per-subject CSV cache and
  `full_course_memory.yaml`, so a disk failure or process exit cannot preserve only part of a
  baseline refresh.
- Decide whether `course_scheduling/report_logging.py` should resolve the repository root with
  `git rev-parse`, or explicitly retain its source-relative bootstrap behavior and document that
  exception to the repository-root rule.
