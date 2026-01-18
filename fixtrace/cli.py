"CLI layer: Typer commands for start, stop, list, generate."

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import json
import threading
import time
import os
import sys
import termios

from typing import List, Optional

from . import session, capture, parser, markdown, ai

app = typer.Typer(help="FixTrace: Capture terminal sessions and auto-generate docs")
console = Console()


def auto_stop_session(session_id, timeout_seconds):
    """Auto-stop a session after timeout expires."""
    time.sleep(timeout_seconds)
    
    # Check if session is still active
    active_id, pid = session.get_active_session()
    if active_id == session_id:
        console.print(f"\n[yellow]⏱️  Session timeout reached ({timeout_seconds}s)[/yellow]")
        console.print("[yellow]Auto-stopping session...[/yellow]")
        
        # Kill the script process - this will cause the main thread to wake up
        if pid and pid > 0:
            try:
                capture.kill_process_by_pid(pid)
            except:
                pass


@app.command()
def start(
    name: str = typer.Option(None, "--name", help="Session name (optional)"),
    timeout: int = typer.Option(None, "--timeout", help="Auto-stop after N seconds (default: from config or 1800 = 30min)"),
):
    """Start a new capture session."""
    # Load config for defaults
    config_file = Path(__file__).parent / ".fixtrace_config.json"
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            pass
    if timeout is None:
        timeout = config.get('timeout', 1800)
    
    try:
        session_id, session_dir = session.create_session(name)
        
        console.print(f"[green]✅ Session started: {session_id}[/green]")
        console.print(f"[dim]Recording to: {session_dir}[/dim]")
        console.print(f"[dim]Auto-stop timeout: {timeout}s ({timeout//60} min)[/dim]")
        console.print(f"[yellow]You are now inside the recording session.[/yellow]")
        console.print(f"[yellow]Type 'exit' or run 'fixtrace stop' in another terminal when done.[/yellow]")
        
        # Start capture - this returns the subprocess
        proc, raw_file = capture.start_capture(session_dir)
        
        if not proc:
            console.print("[red]❌ Failed to start capture process[/red]")
            raise typer.Exit(1)

        # Save session ID and the PID of the CAPTURE process (script)
        session.save_active_pid(session_id, proc.pid)
        
        # Start auto-stop timer in background
        timer_thread = threading.Thread(
            target=auto_stop_session,
            args=(session_id, timeout),
            daemon=True,
        )
        timer_thread.start()
        
        # Save terminal settings
        try:
            old_tty_attrs = termios.tcgetattr(sys.stdin)
        except:
            old_tty_attrs = None
        
        try:
            # Wait for the process to finish (blocking)
            # This will return when user types 'exit' or 'fixtrace stop' kills the process
            proc.wait()
        finally:
            # Restore terminal settings
            if old_tty_attrs:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty_attrs)
        
        # Clear active PID immediately
        session.clear_active_pid()
        
        # Script session ended - parse and generate docs
        if raw_file.exists() and raw_file.stat().st_size > 0:
            console.print(f"\n[green]✅ Session recording ended[/green]")
            
            # Read metadata
            metadata_file = session_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            # Parse
            jsonl_file = session_dir / "events.jsonl"
            console.print("[dim]Parsing session...[/dim]")
            events = parser.parse_raw_to_jsonl(raw_file, jsonl_file)
            
            # Generate Basic Markdown
            console.print("[dim]Saving session...[/dim]")
            md_file = markdown.generate_markdown(session_id, session_dir, metadata)
            
            console.print(f"[green]✅ Session complete![/green]")
            console.print(f"[cyan]Session saved to: {md_file}[/cyan]")
            
            # Ask user if they want to generate AI summary
            response = console.input("[bold]Would you like to generate an AI summary? (yes/no): [/bold]").strip().lower()
            if response in ("yes", "y"):
                with console.status("[bold green]Generating AI summary...[/bold green]"):
                    log_text = parser.build_session_log(events)
                    ai_summary, error = ai.generate_summary(log_text)
                    if ai_summary:
                        md_file = markdown.generate_markdown(session_id, session_dir, metadata, ai_summary=ai_summary)
                        console.print(f"[green]✅ AI summary generated![/green]")
                    else:
                        console.print(f"[red]❌ AI summary failed: {error}[/red]")
    
    except RuntimeError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stop(force: bool = typer.Option(False, "--force", help="Force stop even if process is already dead")):
    """Stop the active capture session."""
    try:
        session_id, pid = session.get_active_session()
        
        if not session_id:
            console.print("[red]❌ No active session running[/red]")
            raise typer.Exit(1)
        
        console.print(f"[yellow]Stopping session {session_id}...[/yellow]")
        
        # Kill the script process
        if pid:
            try:
                capture.kill_process_by_pid(pid)
                console.print(f"[green]Session stopped.[/green]")
                console.print(f"[dim]The original terminal will now process the output.[/dim]")
                
                # Wait a brief moment for the original process to handle cleanup
                time.sleep(0.5)
                
                # Ensure PID file is gone. If the original process didn't clean it up, we do it here.
                # This fixes the issue where 'start' might crash or hang and leave the PID file.
                session.clear_active_pid()
                
            except Exception as e:
                if not force:
                    console.print(f"[red]❌ Error: Process not found. Use --force to clear the session anyway[/red]", err=True)
                    raise typer.Exit(1)
                else:
                    console.print(f"[yellow]⚠ Process already dead, clearing session[/yellow]")
        
        # If forced, we might need to clean up manually, but usually killing the pid is enough.
        if force:
             session.clear_active_pid()
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    name: str = typer.Option(None, "--name", help="Filter sessions by name (partial match, case-insensitive)"),
    status: str = typer.Option(None, "--status", help="Filter sessions by status (exact match, case-insensitive)"),
):
    """List all captured sessions."""
    try:
        sessions = session.list_sessions()
        
        # Apply filters
        if name:
            sessions = [s for s in sessions if name.lower() in s["name"].lower()]
        if status:
            sessions = [s for s in sessions if s["status"].lower() == status.lower()]
        
        if not sessions:
            console.print("[dim]No sessions match the filters[/dim]")
            return
        
        # Sort by started time, newest first
        sessions.sort(key=lambda s: s["started_at"], reverse=True)
        
        table = Table(title="FixTrace Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Name", style="magenta", max_width=15, overflow="ellipsis")
        table.add_column("Started", style="green")
        table.add_column("Status", style="yellow")
        
        for sess in sessions:
            session_dir = session.get_session_dir(sess["session_id"])
            # Hyperlink session ID to folder
            session_id_display = f"[link=file://{session_dir}]{sess['session_id']}[/link]"
            table.add_row(
                session_id_display,
                sess["name"],
                sess["started_at"][:19],
                sess["status"],
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def generate(session_id: str = typer.Argument(..., help="Session ID to regenerate")):
    """Regenerate markdown for a session."""
    try:
        session_dir = session.get_session_dir(session_id)
        
        if not session_dir.exists():
            console.print(f"[red]❌ Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        
        metadata_file = session_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Read events to build log
        jsonl_file = session_dir / "events.jsonl"
        events = parser.parse_jsonl(jsonl_file)
        log_text = parser.build_session_log(events)
        
        with console.status("[bold green]Generating AI summary...[/bold green]"):
            ai_summary, error = ai.generate_summary(log_text)
            if ai_summary:
                md_file = markdown.generate_markdown(session_id, session_dir, metadata, ai_summary=ai_summary)
                console.print(f"[green]✅ Documentation regenerated with AI summary[/green]")
                console.print(f"[cyan]Saved to: {md_file}[/cyan]")
            else:
                console.print(f"[red]❌ AI summary failed: {error}[/red]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def delete(session_id: str = typer.Argument(..., help="Session ID to delete")):
    """Delete a session and its files."""
    try:
        session_dir = session.get_session_dir(session_id)
        
        if not session_dir.exists():
            console.print(f"[red]❌ Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        
        # Confirm deletion
        if not typer.confirm(f"Delete session {session_id}? This cannot be undone."):
            console.print("[dim]Cancelled[/dim]")
            return
        
        import shutil
        shutil.rmtree(session_dir)
        console.print(f"[green]✅ Session deleted: {session_id}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)
    

@app.command()
def config(
    key: str = typer.Argument(..., help="Config key: timeout or output_path"),
    value: str = typer.Argument(None, help="Value to set (omit to get current value)"),
):
    """Get or set configuration values."""
    config_file = Path(__file__).parent / ".fixtrace_config.json"
    config = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except:
            pass
    
    if value is None:
        # Get current value
        if key in config:
            console.print(f"{key}: {config[key]}")
        else:
            console.print(f"{key}: not set")
    else:
        # Set value
        if key == 'timeout':
            try:
                config['timeout'] = int(value)
            except ValueError:
                console.print(f"[red]❌ Invalid value for timeout: must be an integer[/red]")
                raise typer.Exit(1)
        elif key == 'output_path':
            config['output_path'] = value
        else:
            console.print(f"[red]❌ Invalid key: {key}. Use 'timeout' or 'output_path'[/red]")
            raise typer.Exit(1)
        
        # Save config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        console.print(f"[green]✅ Set {key} to {value}[/green]")


@app.command()
def view(session_id: str = typer.Argument(..., help="Session ID to view folder")):
    """Open session folder in Finder (macOS only)."""
    try:
        session_dir = session.get_session_dir(session_id)
        
        if not session_dir.exists():
            console.print(f"[red]❌ Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        
        import subprocess
        subprocess.run(["open", str(session_dir)])
        console.print(f"[green]✅ Opened folder: {session_dir}[/green]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ask(
    question: List[str] = typer.Argument(None, help="Specific question about the session"),
    lines: int = typer.Option(1000, "--lines", "-l", help="Number of recent terminal lines to include as context"),
):
    """Ask AI for help with the current session or a specific question."""
    try:
        # 1. Identify session
        active_id, pid = session.get_active_session()
        if active_id:
            session_id = active_id
            console.print(f"[dim]Using active session: {session_id}[/dim]")
        else:
            # Fallback to latest session
            sessions = session.list_sessions()
            if not sessions:
                console.print("[red]❌ No sessions found.[/red]")
                raise typer.Exit(1)
            # Latest session is first if sorted (session.py doesn't sort, so we do it here or assume latest)
            sessions.sort(key=lambda s: s["started_at"], reverse=True)
            session_id = sessions[0]["session_id"]
            console.print(f"[dim]Using latest session: {session_id}[/dim]")

        # 2. Extract context
        session_dir = session.get_session_dir(session_id)
        console.print(f"[dim]Analyzing last {lines} lines...[/dim]")
        
        raw_content = session.get_recent_log_content(session_dir, lines=lines)
        if not raw_content:
            console.print("[yellow]⚠️ Log is empty or not found.[/yellow]")
            return

        # 3. Clean context (strip ANSI)
        clean_content = parser.clean_text(raw_content)

        # DEBUG: Save context to inspect sanitization
        debug_file = session_dir / "debug_ai_context.txt"
        with open(debug_file, "w") as f:
            f.write(clean_content)
        # console.print(f"[dim]Debug context saved to: {debug_file}[/dim]")

        # 4. Query AI via ai.py
        question_str = " ".join(question) if question else None
        with console.status("[bold green]Asking AI...[/bold green]"):
            response = ai.query_gemini(clean_content, question_str)
        
        console.print(f"\n{response}")

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()