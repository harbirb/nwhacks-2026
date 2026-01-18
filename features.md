# Features

## Core (MVP) - Implemented

- Start session with `fixtrace start` and stop with `fixtrace stop`.
- Passive capture of terminal commands and outputs/errors via `script`.
- Session artifacts stored locally under `~/.fixtrace/sessions/` as JSONL plus generated markdown.
- Basic Markdown doc generation (structured log).
- **LLM-powered summaries** via `fixtrace generate` (using Gemini).
- Session listing with `fixtrace list`.
- Session naming via `--name` flag.

## Nice-to-Have (Backlog)

- Ignore noisy commands (ls, cd, clear) and truncate very long outputs.
- Quick note flag `--note` on stop.
- Copy markdown to clipboard after generation.
- Improved exit-code detection (currently inferred).

## Future (Post-Hackathon)

- Agent/diagnostic mode that runs checks automatically.
- Team sharing/search, cloud storage, analytics, and cross-platform support.
- Advanced secrets redaction beyond basic heuristics.