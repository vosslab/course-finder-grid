# YAML file format

This repository currently uses YAML for generated full-course notification
state. See [FILE_FORMATS.md](FILE_FORMATS.md) for the complete input and output
format inventory.

## Interface boundary

`cache/full_course_memory.yaml` is generated cache state, not user
configuration. The report pipeline reads it before a run and rewrites it after
a non-dry baseline or report run. You may remove the file, or one term entry,
to reset notification memory; routine color or report settings do not belong
in this file.

There is currently no `config_files/subject_colors.yaml` in the repository and
no YAML loader for that path. Subject colors come from the `SUBJECT_HUES`
constant in [course_scheduling/schedule_colors.py](../course_scheduling/schedule_colors.py).
A YAML file placed at `config_files/subject_colors.yaml` therefore has no
effect in the current program. This document does not specify it as a user
configuration interface.

## Full-course memory

### Location and ownership

The email-report path owns `cache/full_course_memory.yaml`. Its canonical path
is `FULL_MEMORY_PATH` in [course_scheduling/csv_cache.py](../course_scheduling/csv_cache.py),
and [course_scheduling/full_course_memory.py](../course_scheduling/full_course_memory.py)
is its reader and writer. `cache/` is gitignored and created by the report
workflow before production writes.

### Canonical schema

```yaml
<term_code>:
  <crn>: <capacity>
```

| Field | Required type | Meaning |
| --- | --- | --- |
| `term_code` | string key | Banner term identifier, such as `"202710"` |
| `crn` | string key | Course Reference Number, such as `"11234"` |
| `capacity` | integer value | Capacity when the section was last reported full |

Use quoted numeric-looking keys. The code looks up terms and CRNs as strings,
so an unquoted YAML numeric key becomes an integer and will not match the
runtime lookup.

```yaml
"202710":
  "11234": 24
  "11235": 36
"202720":
  "21001": 18
```

The writer uses `yaml.safe_dump` with block style and sorted keys. It rewrites
the complete mapping rather than preserving comments, key order, or manual
formatting.

### Read and validation behavior

`load_memory(path)` uses `yaml.safe_load`.

- A missing file returns `{}`.
- An empty file, whose YAML value is `null`, also returns `{}`.
- Invalid YAML raises the PyYAML parser error to the caller.
- A non-empty YAML value is returned as parsed. The loader performs no schema,
  key-type, or capacity-type validation.

The report logic requires the canonical mapping above. A list or scalar cannot
serve as memory because later code reads term entries with `.get()`. Wrong key
types fail to match, and a non-integer capacity can fail the capacity
comparison. Restore the canonical mapping before running the report.

`save_memory(path, memory)` uses `yaml.safe_dump` and overwrites its target. It
does not create a missing parent directory itself; the report workflow creates
`cache/` first.

### Notification semantics

The file records only sections that were full. For each term and CRN it stores
the capacity, not enrollment, title, label, or waitlist count.

- For a term absent from memory, the first report run seeds every currently
  full section and sends no backlog notifications.
- Later, a full CRN absent from that term's mapping emits a notification.
- A remembered CRN emits another notification only when its current full
  capacity is greater than the stored capacity.
- Refilling at the same or a lower capacity is silent.
- Waitlist-only changes do not update this memory.
- A dry run leaves the file unchanged.

After a sent report, the pipeline records fired events and saves the complete
mapping. A baseline refresh also saves silently seeded full sections.

### Reset and repair

- Remove the file to reset all terms. The next run seeds its current full
  sections without email.
- Remove one top-level term key to reset that term only.
- For malformed or incorrectly typed data, replace the file with the canonical
  mapping above, or remove it and let the next non-dry run seed a new baseline.

## Related

- [FILE_FORMATS.md](FILE_FORMATS.md): complete format inventory.
- [USAGE.md](USAGE.md): email-report workflow and notification behavior.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md): first-run notification diagnosis.
