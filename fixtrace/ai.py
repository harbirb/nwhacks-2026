"AI Integration: Handle interactions with Gemini API."

import os
from dotenv import load_dotenv
from google import genai

# Load .env file from current directory or parent directories
load_dotenv()

# Shared prompts
GENERIC_SYSTEM_PROMPT = """
You are an expert CLI developer assistant named FixTrace.
Your goal is to help developers debug errors and understand their terminal sessions.
You are provided with the raw text output from a terminal session.

IMPORTANT: 
- The logs may contain previous calls to `fixtrace ask` and your own previous responses. 
- IGNORE these previous Q&A interactions. 
- Focus ONLY on the actual shell commands and system outputs that occurred before the most recent `fixtrace` invocation.
- Do not analyze `fixtrace` commands themselves unless the user specifically asks about them.
"""

SUGGESTION_PROMPT = """
Analyze the provided terminal logs and:
1. Identify the most recent error or failed command.
2. Explain the error briefly (1-2 sentences).
3. Provide the EXACT shell command to fix it.

Format your response exactly as follows:
💡 Analysis:
<Explanation>

🚀 Suggestion:
<Command>

If no clear error is found, say: "No error detected in the recent logs."
"""

QA_PROMPT = """
Answer the user's question based on the provided terminal logs.
Be concise and specific. Quote parts of the log if relevant.

Format your response as:
💬 Answer:
<Your answer>
"""

SUMMARY_PROMPT = """
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
- If secrets appear, replace them with descriptive placeholders like:
  - API keys → [YOUR-API-KEY-HERE]
  - Tokens → [YOUR-TOKEN-HERE]
  - Passwords → [YOUR-PASSWORD-HERE]
  - Database URLs → [YOUR-DATABASE-URL-HERE]
  - Other secrets → [YOUR-SECRET-HERE]
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

def _get_client():
    """Initialize and return the Gemini client."""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)

def _call_gemini(full_prompt):
    """Helper to call Gemini API with error handling."""
    try:
        client = _get_client()
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

def query_gemini(context_text, user_question=None):
    """Query Gemini with session context and optional user question.
    
    Args:
        context_text (str): The raw terminal output to analyze.
        user_question (str, optional): Specific question from the user.
                                     If None, defaults to error analysis/fix suggestion.
    
    Returns:
        str: The AI's response text.
    """
    if user_question:
        instruction = f"{QA_PROMPT}\n\nUSER QUESTION:\n{user_question}"
    else:
        instruction = SUGGESTION_PROMPT
        
    full_prompt = f"{GENERIC_SYSTEM_PROMPT}\n\nTERMINAL LOGS:\n{context_text}\n\nINSTRUCTIONS:\n{instruction}"
    return _call_gemini(full_prompt)

def generate_summary(session_log):
    """Generate a structured summary of the session using Gemini.
    
    Args:
        session_log (str): The readable session log.
    
    Returns:
        tuple: (summary_text, error_message)
    """
    try:
        full_prompt = SUMMARY_PROMPT + session_log
        
        # We use _get_client here directly to handle exceptions differently
        # (returning None, error string instead of an error string content)
        client = _get_client()
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=full_prompt
        )
        return response.text, None
        
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, f"Gemini API error: {str(e)}"