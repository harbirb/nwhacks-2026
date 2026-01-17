"""Capture engine: wrap script subprocess for terminal I/O capture."""

import subprocess
import signal
import os
from pathlib import Path


def start_capture(session_dir):
    """Start script capture by calling it directly (non-blocking).
    
    The script command will take over the current shell and record to raw_file.
    The user will interact with the script session directly.
    """
    raw_file = session_dir / "raw.txt"
    
    # Start script command - this replaces the current shell
    # The user is now inside the script session
    os.system(f"script -q {raw_file}")
    
    return None, raw_file


def stop_capture(proc):
    """Legacy function - not used with new implementation."""
    pass


def kill_process_by_pid(pid):
    """Kill a process by PID gracefully."""
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait a bit for graceful shutdown
        import time
        time.sleep(0.5)
    except OSError:
        pass  # Already dead
    except Exception as e:
        print(f"Warning: Error killing process: {e}")
