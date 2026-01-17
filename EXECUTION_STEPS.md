# FixTrace MVP - Execution Steps

## Setup & Installation

### 1. Navigate to project directory

```bash
cd /Users/harbir/Projects/nwhacks-2026
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

This creates an isolated Python environment for the project.

### 3. Activate the virtual environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` at the beginning of your terminal prompt.

### 4. Install dependencies

```bash
pip install -e .
```

This will install:

- `typer` - CLI framework
- `rich` - Terminal UI
- The `fixtrace` command globally within this venv

### 5. Verify installation

```bash
fixtrace --help
```

**Expected output:**

```
Usage: fixtrace [OPTIONS] COMMAND [ARGS]...

FixTrace: Capture terminal sessions and auto-generate docs

Options:
  --help  Show this message and exit.

Commands:
  generate  Regenerate markdown for a session.
  list      List all captured sessions.
  start     Start a new capture session.
  stop      Stop the active capture session and generate docs.
```

### 6. Add fixtrace to PATH (so it works from anywhere)

Open your shell configuration file:

```bash
nano ~/.zshrc
```

Add this line at the bottom:

```bash
export PATH="/Users/harbir/Projects/nwhacks-2026/.venv/bin:$PATH"
```

Save the file (Ctrl+X, then Y, then Enter).

Reload your shell:

```bash
source ~/.zshrc
```

Now `fixtrace` will work from **any directory**!

### 7. Update .gitignore (optional but recommended)

Add this to your `.gitignore` to keep the venv out of git:

```
.venv/
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.DS_Store
```

### 8. Verify PATH setup

Test that fixtrace works from anywhere:

```bash
cd ~
fixtrace --help
```

If you see the help output, you're all set! ✅

### 9. Deactivate venv (when done with work)

To exit the virtual environment later:

```bash
deactivate
```

To reactivate it later:

```bash
source .venv/bin/activate
```

**Note**: With the PATH setup, you don't _need_ to activate the venv, but it's good practice for development.

---

## Testing the MVP

### Test 1: Basic start/stop workflow

```bash
# Start a capture session
fixtrace start --name "test-session"
```

**Expected output:**

```
✅ Session started: 2026-01-17-abc123
Recording to: /Users/harbir/.fixtrace/sessions/2026-01-17-abc123
Run 'fixtrace stop' when done
```

The command will now be recording your terminal. The prompt will change - you're now inside a `script` session.

```bash
# Run some test commands
ls -la
echo "Hello from FixTrace"
pwd

# Try a failing command to test error capture
nonexistent_command

# Fix it
echo "Fixed!"

# Exit the script session to stop recording
exit
```

**Expected output after exit:**

```
Stopping session 2026-01-17-abc123...
Parsing session...
Generating documentation...
✅ Session complete!
Docs saved to: /Users/harbir/.fixtrace/sessions/2026-01-17-abc123/README.md
```

### Test 2: View generated documentation

```bash
cat ~/.fixtrace/sessions/2026-01-17-abc123/README.md
```

You should see a markdown file with:

- Session name and metadata
- Each command you ran in code blocks
- The output of each command

### Test 3: List sessions

```bash
fixtrace list
```

**Expected output:**

```
                        FixTrace Sessions
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
┃ Session ID           ┃ Name         ┃ Started        ┃ Status      ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
│ 2026-01-17-abc123    │ test-session │ 2026-01-17 ... │ ✅ Complete │
└──────────────────────┴──────────────┴────────────────┴─────────────┘
```

### Test 4: Regenerate markdown for a session

```bash
fixtrace generate 2026-01-17-abc123
```

**Expected output:**

```
Generating documentation...
✅ Documentation regenerated
Saved to: /Users/harbir/.fixtrace/sessions/2026-01-17-abc123/README.md
```

---

## Real-world testing scenario

Try this more realistic example:

```bash
# Start capturing a "broken setup" scenario
fixtrace start --name "npm-setup-fix"

# Simulate broken npm
npm install

# See the error (likely permission denied)
# Try to fix it
sudo npm install

# Verify it works
npm list

# Done
exit
```

Then check the generated markdown to see how it captured your troubleshooting process!

---

## Troubleshooting

### "script: command not found"

You're on a system without `script`. This is built into macOS, so this shouldn't happen on Mac.

### "No active session running"

Make sure you ran `fixtrace start` before running `fixtrace stop`.

### Session not appearing in `fixtrace list`

Check that `README.md` was generated:

```bash
ls -la ~/.fixtrace/sessions/
```

### Raw output looks garbled

This is expected - raw.txt has ANSI escape codes. The events.jsonl and README.md should be clean.

---

## Files created

After running through these tests, you should have:

```
~/.fixtrace/
├── active_session.pid  (only while recording)
└── sessions/
    └── 2026-01-17-abc123/
        ├── metadata.json   (session info)
        ├── raw.txt        (raw script output)
        ├── events.jsonl   (parsed events)
        └── README.md      (generated docs)
```

---

## Next steps for the team

1. **Test the basic workflow** using the steps above
2. **Identify parsing issues** - the command grouping heuristic is basic
3. **Improve ANSI stripping** if needed
4. **Add error detection** to better infer root cause
5. **Refine markdown template** for better readability
6. **Add LLM integration** (post-MVP)

Good luck! 🚀
