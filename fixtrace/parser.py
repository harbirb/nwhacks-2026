"""Parser: strip ANSI codes, group commands/outputs, emit JSONL events."""

import re
import json
from pathlib import Path
from datetime import datetime


def clean_text(text):
    """Remove ANSI escape codes and handle backspaces."""
    # 1. Strip OSC sequences (Operating System Commands)
    # Matches \x1B] ... \x07 or \x1B\
    osc_escape = re.compile(r'\x1B\].*?(?:\x07|\x1B\\)')
    text = osc_escape.sub('', text)

    # 2. Strip standard ANSI escape sequences (CSI codes, etc.)
    # Matches \x1B followed by [...] or other terminator
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # 3. Handle backspaces (common in raw terminal capture)
    # If we encounter a backspace, remove the previous character
    chars = []
    for c in text:
        if c == '\x08':
            if chars:
                chars.pop()
        else:
            chars.append(c)
    
    return "".join(chars)


def parse_raw_to_jsonl(raw_file, jsonl_file):
    """Parse raw script output to JSONL events.
    
    Handles:
    - zsh (%) and bash ($/#) prompts
    - ANSI color stripping
    - Backspace correction
    - Command/Output grouping
    """
    
    with open(raw_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Clean the raw content
    content = clean_text(content)
    
    lines = content.split('\n')
    
    events = []
    current_command = None
    current_output = []
    
    # Regex to detect prompts at the start of a line
    # Matches:
    # - standard: user@host:path$ 
    # - zsh: path % 
    # - simple: $ 
    # It looks for a sequence ending in $, #, or % followed by whitespace
    # We use a non-greedy match for the prefix to avoid capturing too much
    prompt_re = re.compile(r'^.*?(?:[\w\.~/@:-]+)\s*[\$#%]\s+(.*)$')
    
    # Fallback for just a symbol prompt
    simple_prompt_re = re.compile(r'^[\$#%]\s+(.*)$')

    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for prompt
        match = prompt_re.match(line) or simple_prompt_re.match(line)
        
        if match:
            # We found a new command line
            
            # 1. Save the PREVIOUS command/output pair
            if current_command:
                events.append({
                    "type": "command",
                    "timestamp": datetime.now().isoformat(),
                    "command": current_command,
                })
                # Only add output if there is something substantial
                if current_output:
                    events.append({
                        "type": "output",
                        "timestamp": datetime.now().isoformat(),
                        "content": "\n".join(current_output).strip(),
                    })
                current_output = []
            
            # 2. Start the NEW command
            # The regex capture group (1) contains the command text after the prompt
            cmd_text = match.group(1).strip()
            
            # If the command is empty, it might be just a hit enter
            current_command = cmd_text if cmd_text else " " 
            
        else:
            # This line does not look like a prompt, assume it's output
            # (Only if we have seen a command already, or just capture everything)
            if current_command is not None:
                current_output.append(line)
            # If we haven't seen a command yet, it's probably pre-session noise or header
            # We can ignore it or add it to a "header" event if we wanted.
    
    # Save the LAST command/output pair
    if current_command:
        events.append({
            "type": "command",
            "timestamp": datetime.now().isoformat(),
            "command": current_command,
        })
        if current_output:
            events.append({
                "type": "output",
                "timestamp": datetime.now().isoformat(),
                "content": "\n".join(current_output).strip(),
            })
    
    # Write JSONL
    with open(jsonl_file, 'w') as f:
        for event in events:
            f.write(json.dumps(event) + '\n')
    
    return events


def parse_jsonl(jsonl_file):
    """Read JSONL file and return list of events."""
    events = []
    try:
        with open(jsonl_file, 'r') as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    except FileNotFoundError:
        pass
    
    return events


def build_session_log(events):
    """Build a readable session log from events."""
    log_lines = []
    for event in events:
        if event.get('type') == 'command':
            log_lines.append(f"$ {event.get('command', '')}")
        elif event.get('type') == 'output':
            content = event.get('content', '')
            if content:
                log_lines.append(content)
    return '\n'.join(log_lines)
