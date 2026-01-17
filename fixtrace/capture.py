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
    
    # Determine flags based on platform
    # macOS uses -F for immediate flush, Linux uses -f
    import sys
    flush_flag = "-F" if sys.platform == "darwin" else "-f"
    
    # Start script command using Popen to capture the process ID
    # This allows us to kill the specific 'script' process later
    try:
        proc = subprocess.Popen(
            ["script", "-q", flush_flag, str(raw_file)],
            stdin=None,  # Inherit stdin
            stdout=None, # Inherit stdout
            stderr=None, # Inherit stderr
            preexec_fn=os.setsid # Start in new session to avoid signal propagation issues
        )
        return proc, raw_file
    except Exception as e:
        print(f"Error starting capture: {e}")
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
