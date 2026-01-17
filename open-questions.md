# Open Questions

- Should we auto-name sessions or prompt for a name by default? (Currently: auto with optional --name.)
- Which commands to ignore by default (ls, cd, clear) and should this be configurable?
- Output limits per command (e.g., truncate after N lines) to prevent runaway logs?
- How to tag the problem statement/root cause: heuristic only or ask user for a short note on stop?
- Minimal secret redaction policy: filter password prompts only, or broader patterns?
- Do we require timestamps on every event, or is per-command sufficient for readability?
