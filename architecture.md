# Architecture Snapshot

## Components

- CLI layer: Typer commands (`start`, `stop`, `list`, `generate`).
- Session manager: IDs, PID tracking, paths, and lifecycle.
- Capture engine: wraps `script` subprocess for terminal I/O capture.
- Parser: strips ANSI, groups commands/outputs, emits JSONL events.
- Markdown generator: templates to produce doc-ready output from events.

## Data Flow

1. start → spawn `script` → raw capture file.
2. stop → parse raw → JSONL events.
3. generate → markdown doc.

## File Paths

- `~/.fixtrace/sessions/<session-id>.jsonl` (raw events).
- `~/.fixtrace/sessions/<session-id>.md` (generated docs).
- Optional PID file to guard single active session.
