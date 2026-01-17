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

- `~/.fixtrace/sessions/<session-id>/` (session folder).
- `~/.fixtrace/sessions/<session-id>/raw.txt` (raw script output).
- `~/.fixtrace/sessions/<session-id>/events.jsonl` (parsed events).
- `~/.fixtrace/sessions/<session-id>/README.md` (generated docs).
- `~/.fixtrace/active_session.pid` (tracks current session: `<session-id>:<pid>`).

## Session Lifecycle & PID Tracking

### Why PID Tracking?

When `fixtrace start` launches a `script` process in the background, we need to know:
- Is a session currently active?
- Which process should `fixtrace stop` terminate?

PID tracking via a persistent file on disk solves this.

### Lifecycle Flow

```
[1] fixtrace start
    ↓
    • Generate session ID (e.g., "2026-01-17-abc123")
    • Create folder: ~/.fixtrace/sessions/2026-01-17-abc123/
    • Spawn `script` process, get PID (e.g., 12345)
    • Write PID file: ~/.fixtrace/active_session.pid
      Content: "2026-01-17-abc123:12345"
    • Start recording to: ~/.fixtrace/sessions/2026-01-17-abc123/raw.txt
    ✅ Return: "Session started: 2026-01-17-abc123"

[2] User troubleshoots (script records silently in background)

[3] fixtrace stop
    ↓
    • Read PID file: ~/.fixtrace/active_session.pid
    • Extract session ID + PID (e.g., "abc123:12345")
    • Send SIGTERM to process 12345 (graceful shutdown)
    • Delete PID file
    • Trigger parser + markdown generator
    ✅ Return: "Session saved to ~/.fixtrace/sessions/2026-01-17-abc123/README.md"

[4] fixtrace list
    ↓
    • Scan ~/.fixtrace/sessions/
    • For each session, check if README.md exists (complete) or if active_session.pid references it (running)
    ✅ Return: table of all sessions
```

### Cross-Terminal Safety

The PID file on disk enables **seamless terminal switching**:

```bash
# Terminal 1
$ fixtrace start
✅ Session abc123 started
# (PID file written to disk)

# Close Terminal 1, open Terminal 2
$ fixtrace stop
# Still works! Reads PID file from disk, kills the process
```

The `script` process runs independently of which terminal started it, so any terminal can stop it by reading the PID from disk.

### Conflict Prevention

```bash
$ fixtrace start
✅ Session abc123 started

$ fixtrace start  # Oops, forgot to stop
❌ Error: Session abc123 already running!
   Stop it with: fixtrace stop
```

Session manager checks for an existing PID file before starting a new session.
