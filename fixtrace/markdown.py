"""Markdown generator: templates to produce doc-ready output from events."""

from pathlib import Path
from datetime import datetime
import json
import os

from dotenv import load_dotenv
from google import genai

# Load .env file from current directory or parent directories
load_dotenv()


GEMINI_PROMPT = """
You are a software engineer helping document a debugging session. The input is a raw terminal log recorded whilesetting up or debugging a project.
It may contain failed commands, repeated attempts, error messages, and unrelated shell output.

Your job is to:
- Identify the actual problem the developer was trying to solve
- Pick out the commands that mattered
- Summarize the errors that blocked progress
- Explain the steps that ultimately fixed the issue

Focus on high-signal information only.
Write the summary so that a future developer could understand what went wrong and how to fix it, without reading the full terminal log.

Review the debugging session and generate a short, structured summary that explains:
- What problem was being faced
- Which commands were important
- What errors occurred
- What steps resolved the issue

Rules:
- Ignore duplicated commands unless they show a before/after fix.
- Ignore shell noise, prompts, timestamps, and unrelated output.
- Do NOT include secrets, tokens, credentials, or environment values.
- If secrets appear, replace them with "[REDACTED]".
- Be factual: only infer causes if strongly supported by the session.
- If the root cause is unclear, say "Root cause not definitively identified".
- Use clear, simple language suitable for onboarding documentation.

Output exactly in the following format:

🛠 FixTrace Summary

Problem:
- <1–2 bullet points>

Key Commands:
- <command>
- <command>

Errors Encountered:
- <short description of error>
- <short description of error>

Resolution Steps:
1. <step>
2. <step>

Root Cause:
- <single concise explanation>

Notes:
- <optional insights, gotchas, or onboarding tips>

Do not include any text outside this format.

---

Here is the terminal session log: 

"""


def _build_session_log(events):
    """Build a readable session log from events for Gemini to analyze."""
    log_lines = []
    for event in events:
        if event.get('type') == 'command':
            log_lines.append(f"$ {event.get('command', '')}")
        elif event.get('type') == 'output':
            content = event.get('content', '')
            if content:
                log_lines.append(content)
    return '\n'.join(log_lines)


def _generate_summary_with_gemini(session_log):
    """Use Gemini API to generate a summary of the session."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None, "GEMINI_API_KEY environment variable not set"
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = GEMINI_PROMPT + session_log
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        
        return response.text, None
    except Exception as e:
        return None, f"Gemini API error: {str(e)}"


def generate_markdown(session_id, session_dir, metadata, use_ai=False):
    """Generate markdown documentation from captured session.
    
    Args:
        session_id: The session identifier
        session_dir: Path to the session directory
        metadata: Session metadata dict
        use_ai: Whether to generate AI summary (default: False)
    """
    
    jsonl_file = session_dir / "events.jsonl"
    markdown_file = session_dir / "summary.md"
    
    # Parse events
    events = []
    try:
        with open(jsonl_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    except FileNotFoundError:
        events = []
    
    # Build session log for Gemini
    session_log = _build_session_log(events)
    
    # Try to generate AI summary only if requested
    ai_summary = None
    error = None
    if use_ai:
        ai_summary, error = _generate_summary_with_gemini(session_log)
    
    # Build markdown
    md_lines = []
    md_lines.append(f"# Troubleshooting Session: {metadata.get('name', session_id)}")
    md_lines.append("")
    
    # Metadata
    started_at = metadata.get('started_at', '')
    md_lines.append(f"**Date**: {started_at[:10]}")
    md_lines.append(f"**Session ID**: {session_id}")
    md_lines.append("")
    
    # AI-generated summary
    if ai_summary:
        md_lines.append(ai_summary)
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
    elif error:
        md_lines.append(f"> ⚠️ AI summary unavailable: {error}")
        md_lines.append("")
    
    # Commands and outputs (raw log)
    md_lines.append("## Raw Session Log")
    md_lines.append("")
    
    step_num = 0
    for i, event in enumerate(events):
        if event.get('type') == 'command':
            step_num += 1
            command = event.get('command', '')
            md_lines.append(f"### Step {step_num}")
            md_lines.append("")
            md_lines.append("```bash")
            md_lines.append(command)
            md_lines.append("```")
            md_lines.append("")
            
            # Look for output after this command
            if i + 1 < len(events) and events[i + 1].get('type') == 'output':
                output = events[i + 1].get('content', '')
                if output:
                    md_lines.append("**Output:**")
                    md_lines.append("")
                    md_lines.append("```")
                    md_lines.append(output)
                    md_lines.append("```")
                    md_lines.append("")
    
    # Footer
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*Generated by FixTrace*")
    md_lines.append("")
    
    # Write markdown
    with open(markdown_file, 'w') as f:
        f.write('\n'.join(md_lines))
    
    return markdown_file
