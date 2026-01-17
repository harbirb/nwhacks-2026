"""Capture engine: wrap script subprocess for terminal I/O capture."""

import subprocess
import signal
import os
from pathlib import Path


def start_capture(session_dir):
    """Start script capture. Returns the subprocess and raw output path."""
    raw_file = session_dir / "raw.txt"
    
    # Start script command to record terminal session
    proc = subprocess.Popen(
        ["script", "-q", str(raw_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    return proc, raw_file


def stop_capture(proc):
    """Stop the capture process gracefully."""
    try:
        # Send Ctrl+D (EOF) to exit the shell
        proc.stdin.write(b"exit\n")
        proc.stdin.flush()
        
        # Wait for process to exit
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        # Force kill if timeout
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    except Exception as e:
        print(f"Warning: Error stopping capture: {e}")
        try:
            proc.kill()
        except:
            pass


def kill_process_by_pid(pid):
    """Kill a process by PID."""
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait a bit for graceful shutdown
        try:
            import time
            time.sleep(1)
        except:
            pass
    except ProcessNotFoundError:
        pass  # Already dead
    except Exception as e:
        print(f"Warning: Error killing process: {e}")
