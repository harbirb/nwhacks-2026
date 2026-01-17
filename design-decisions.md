# Design Decisions

## Capture Strategy

- **Passive capture with `script`**: Built into macOS, captures commands and output reliably; fastest path for a 24h MVP.
- **Session boundary via start/stop**: Explicit `fixtrace start`/`stop` avoids ambiguous shell history and lets us attach metadata (name, note).

## Data & Storage

- **JSONL raw log**: Append-only, resilient if the process dies, easy to parse/stream later.
- **Local storage under `~/.fixtrace/`**: No external dependencies; keeps hackathon scope tight.
- **Markdown generation on stop**: Auto-generate doc immediately so users get value without extra steps.

## Output & Parsing

- **ANSI stripping**: Remove escape codes so markdown stays readable.
- **Heuristic command grouping**: Use prompt-like regex to split commands; accept minor inaccuracies for MVP.
- **Limited exit-code fidelity**: `script` does not capture exit codes cleanly; infer from stderr or accept limitation.

## Non-Goals for MVP

- Agent mode, real-time suggestions, cloud sync, or Windows support.
- Bulletproof secret scrubbing (basic password-line redaction only).
