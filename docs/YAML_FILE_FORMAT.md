# YAML file format

Specification for the runtime YAML state file used by the full-course memory subsystem.

## File

`cache/full_course_memory.yaml`

Written and read by `course_scheduling/full_course_memory.py`. The path is defined in
`course_scheduling/csv_cache.py` as `FULL_MEMORY_PATH`. The file is gitignored.

## Purpose

Prevents false-positive "section now full" emails. When a section that was already
reported full loses a seat and refills at the same capacity, the memory suppresses
the redundant notification. A genuine capacity increase (for example 24 -> 36) fires
a new event with a `(was full at PREV)` note in the email body.

## Schema

```yaml
<term_code>:
  <crn>: <capacity>
```

- `term_code`: Banner term identifier string, for example `"202710"`.
- `crn`: Course Reference Number string, for example `"12345"`.
- `capacity`: Integer enrollment capacity at the time the section was last reported full.

### Example

```yaml
"202710":
  "11234": 24
  "11235": 36
"202720":
  "21001": 18
```

## Semantics

- Missing file: treated as empty memory; the first run seeds silently (no flood of
  "full" emails on the first run for a new term).
- Empty file: parsed as an empty dict via `yaml.safe_load` null normalization.
- A CRN absent from memory fires the "now full" event when detected as full.
- A CRN present fires again only when `current_capacity > remembered_capacity`.
- Waitlist enrollment changes are noise and do not write to memory.

## Operations

| Function | Behavior |
| --- | --- |
| `load_memory(path)` | Returns the mapping, or `{}` when file is absent or empty |
| `save_memory(path, memory)` | Writes with `yaml.safe_dump`; keys sorted; no flow style |
| `detect_full_events(rows, term_code, memory)` | Returns events; does not update memory |
| `record_full_events(memory, term_code, events)` | Records fired events into the mapping in place; returns `None` |
| `seed_full_sections(rows, term_code, memory)` | Seeds every currently-full section without firing events; returns `None` |

## Reset

- Delete the file to reset memory for all terms.
- Remove a single top-level key to reset one term only.

## Related

- [USAGE.md](USAGE.md): full-course memory semantics in the user workflow context.
- [FILE_FORMATS.md](FILE_FORMATS.md): all input and output file formats.
