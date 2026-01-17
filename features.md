# Features

## Core (MVP)

- Start session with `fixtrace start` and stop with `fixtrace stop`.
- Passive capture of terminal commands and outputs/errors via `script`.
- Session artifacts stored locally under `~/.fixtrace/sessions/` as JSONL plus generated markdown.
- Markdown doc includes problem statement, ordered steps (command + output), inferred root cause, and final fix.

## Nice-to-Have (if time permits)

- Ignore noisy commands (ls, cd, clear) and truncate very long outputs.
- Session naming flag `--name` and quick note flag `--note` on stop.
- Copy markdown to clipboard after generation; timestamped file naming.
- `fixtrace list` to view past sessions and statuses.

## Future (post-hackathon)

- LLM-powered summaries and problem detection.
- Agent/diagnostic mode that runs checks automatically.
- Team sharing/search, cloud storage, analytics, and cross-platform support.
- Better exit-code detection and secrets redaction beyond basic heuristics.
