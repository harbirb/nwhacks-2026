"""Session management: IDs, PID tracking, paths, and lifecycle."""

import os
import json
from pathlib import Path
from datetime import datetime
import random
import string

HOME = Path.home()
FIXTRACE_DIR = HOME / ".fixtrace"
SESSIONS_DIR = FIXTRACE_DIR / "sessions"
ACTIVE_PID_FILE = FIXTRACE_DIR / "active_session.pid"


def ensure_dirs():
    """Create necessary directories if they don't exist."""
    FIXTRACE_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)


def generate_session_id():
    """Generate a unique session ID: YYYY-MM-DD-abc123."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{date_str}-{random_suffix}"


def create_session(name=None):
    """Create a new session. Returns (session_id, session_dir)."""
    ensure_dirs()
    
    # Check if session already running
    if ACTIVE_PID_FILE.exists():
        raise RuntimeError(
            f"Session already running. Stop it first with: fixtrace stop"
        )
    
    session_id = generate_session_id()
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    # Store metadata
    metadata = {
        "session_id": session_id,
        "name": name or session_id,
        "started_at": datetime.now().isoformat(),
    }
    
    metadata_file = session_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    return session_id, session_dir


def save_active_pid(session_id, pid):
    """Write active session PID file: session_id:pid."""
    ensure_dirs()
    with open(ACTIVE_PID_FILE, "w") as f:
        f.write(f"{session_id}:{pid}")


def get_active_session():
    """Read active session info. Returns (session_id, pid) or (None, None)."""
    if not ACTIVE_PID_FILE.exists():
        return None, None
    
    try:
        with open(ACTIVE_PID_FILE, "r") as f:
            content = f.read().strip()
            session_id, pid = content.split(":")
            return session_id, int(pid)
    except (ValueError, IOError):
        return None, None


def clear_active_pid():
    """Delete the active PID file."""
    if ACTIVE_PID_FILE.exists():
        ACTIVE_PID_FILE.unlink()


def get_session_dir(session_id):
    """Get the session directory path."""
    return SESSIONS_DIR / session_id


def list_sessions():
    """List all sessions with metadata."""
    ensure_dirs()
    sessions = []
    
    if not SESSIONS_DIR.exists():
        return sessions
    
    for session_dir in sorted(SESSIONS_DIR.iterdir(), reverse=True):
        if not session_dir.is_dir():
            continue
        
        metadata_file = session_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
            
            # Check if complete
            has_markdown = (session_dir / "README.md").exists()
            
            sessions.append({
                "session_id": metadata["session_id"],
                "name": metadata.get("name", metadata["session_id"]),
                "started_at": metadata.get("started_at", ""),
                "status": "✅ Complete" if has_markdown else "⏳ In Progress",
            })
    
    return sessions
