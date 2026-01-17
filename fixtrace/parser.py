"""Parser: strip ANSI codes, group commands/outputs, emit JSONL events."""

import re
import json
from pathlib import Path
from datetime import datetime


def strip_ansi(text):
    """Remove ANSI escape codes from text."""
    ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_escape.sub('', text)


def parse_raw_to_jsonl(raw_file, jsonl_file):
    """Parse raw script output to JSONL events.
    
    Simple approach: group lines by command prompts.
    A prompt looks like: user@host:path$
    """
    
    with open(raw_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Strip ANSI codes
    content = strip_ansi(content)
    
    # Split by common shell prompts
    # This is a heuristic: look for lines ending with $ or #
    lines = content.split('\n')
    
    events = []
    current_command = None
    current_output = []
    
    for line in lines:
        # Detect command line (ends with $ or #, or looks like a prompt)
        if re.search(r'[\$#]\s*$', line.strip()):
            # Save previous command if any
            if current_command:
                events.append({
                    "type": "command",
                    "timestamp": datetime.now().isoformat(),
                    "command": current_command.strip(),
                })
                if current_output:
                    events.append({
                        "type": "output",
                        "timestamp": datetime.now().isoformat(),
                        "content": "\n".join(current_output).strip(),
                    })
                current_output = []
            
            # Extract command (remove prompt)
            current_command = re.sub(r'.*[\$#]\s*', '', line)
        else:
            # This is output
            if current_command is not None or line.strip():
                current_output.append(line)
    
    # Save last command
    if current_command:
        events.append({
            "type": "command",
            "timestamp": datetime.now().isoformat(),
            "command": current_command.strip(),
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
