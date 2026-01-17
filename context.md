# FixTrace Context

A CLI tool to passively capture terminal troubleshooting sessions for onboarding/development teams on macOS, then auto-generate step-by-step markdown docs (problem, steps, root cause, fix). MVP is passive capture only; future phases add LLM summaries and agent diagnostics.

## Users & Use Case

- New devs following outdated setup docs; need actionable, current fixes.
- Teams want frictionless knowledge capture without manual note-taking.

## Core Workflow (MVP)

- `fixtrace start [--name]` → run troubleshooting commands normally.
- `fixtrace stop [--note]` → stop capture, parse, and emit markdown locally.
- Artifacts live in `~/.fixtrace/sessions/` (JSONL raw + generated .md).

## Operating Assumptions

- macOS, zsh/bash shells; 24-hour hackathon scope; local-only storage.
- Accept imperfect exit-code detection and heuristic command grouping for speed.
