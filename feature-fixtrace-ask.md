# Feature Specification: `fixtrace ask`

## 1. Objective
Enable developers to query an AI assistant using their active terminal session as context. The `fixtrace ask` command allows users to get immediate help with errors (default behavior) or ask specific questions about the session state without copy-pasting logs.

## 2. User Experience

**Scenario A: Auto-Fix (No argument)**
1. User hits an error.
2. User runs: `fixtrace ask`
3. **Output:**
   ```text
   Analyzing recent session output...
   
   💡 Analysis:
   The error 'Connection refused' indicates the server isn't running on port 8000.
   
   🚀 Suggestion:
   Start the server with `uvicorn main:app --reload`
   ```

**Scenario B: Specific Question**
1. User sees an output they don't understand (not necessarily an error).
2. User runs: `fixtrace ask "Where is the config file being loaded from?"`
3. **Output:**
   ```text
   Analyzing context...
   
   💬 Answer:
   Based on the log line `[INFO] Loading config from /etc/myapp/config.yaml`, your configuration is being loaded from the system directory, not your local project.
   ```

## 3. Technical Implementation

### A. CLI Command (`fixtrace/cli.py`)
- **Command:** `ask`
- **Arguments:**
  - `question` (Optional, `str`): The user's query. If omitted, defaults to "Identify the last error and suggest a fix."
  - `--lines` (Optional, `int`, default: 50): Number of lines of context to include.

### B. Context & Logic
1. **Identify Session:**
   - Check `active_session.pid`. If active, use that session.
   - If inactive, use the latest session in `~/.fixtrace/sessions/`.
2. **Read Context:**
   - Read the tail of `raw.txt`.
   - Strip ANSI codes (`parser.clean_text`).
3. **Construct Prompt:**
   - **System:** "You are an expert CLI developer assistant. You are provided with the recent terminal output of a user's session."
   - **Context:** `[TERMINAL LOGS] ...`
   - **User Input:**
     - *If question provided:* "Answer this question based on the logs: {question}"
     - *If no question:* "Identify the most recent error or issue in these logs. Explain it briefly and provide the specific shell command to fix it."

### C. AI Integration (`fixtrace/ai.py`)
- Extract Gemini client setup into this new module.
- Implement a generic `query_gemini(context_text, user_prompt)` function.
- Handle API keys via `os.environ` (load from `.env`).

## 4. Execution Plan

1.  **Refactor:** Create `fixtrace/ai.py` and move the `genai` import/setup there from `markdown.py`.
2.  **Logic:** Add `get_recent_log_content(session_dir, lines)` to `fixtrace/session.py`.
3.  **CLI:** Implement the `ask` command in `fixtrace/cli.py`.
4.  **Prompting:** Tune the prompts for the two distinct modes (fix vs. answer).

## 5. Constraints
- **Privacy:** warn if potential secrets (env vars, keys) are found in the context window.
- **Latency:** Must be fast (<3s). Use a faster model (Gemini Flash) if possible.
