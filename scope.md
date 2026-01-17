# Scope & Timeline (24h Hackathon)

## Must-Haves

- Start/stop capture; store raw session output locally.
- Parse into structured JSONL; generate readable markdown (steps, outputs, inferred root cause/fix).
- Basic ANSI stripping and minimal error handling.

## Nice-to-Haves (time-boxed)

- Command noise filtering; output truncation; session naming/notes.
- `fixtrace list` and clipboard copy for markdown.

## Phased Plan

- Hours 0-6: Project setup; spike `script`; implement start/stop + file write.
- Hours 6-14: Parsing (ANSI strip, command grouping) and markdown generation.
- Hours 14-20: CLI polish (list/status, flags), testing on zsh/bash, edge cases.
- Hours 20-24: Demo scenario, README updates, formatting polish.
