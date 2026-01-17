"""CLI layer: Typer commands for start, stop, list, generate."""

import typer
from rich.console import Console
from rich.table import Table
from pathlib import Path
import json

from . import session, capture, parser, markdown

app = typer.Typer(help="FixTrace: Capture terminal sessions and auto-generate docs")
console = Console()


@app.command()
def start(name: str = typer.Option(None, "--name", help="Session name (optional)")):
    """Start a new capture session."""
    try:
        session_id, session_dir = session.create_session(name)
        
        console.print(f"[green]✅ Session started: {session_id}[/green]")
        console.print(f"[dim]Recording to: {session_dir}[/dim]")
        
        # Start capture
        proc, raw_file = capture.start_capture(session_dir)
        
        # Save active PID
        session.save_active_pid(session_id, proc.pid)
        
        console.print(f"[dim]Run 'fixtrace stop' when done[/dim]")
        
        # Keep process alive
        proc.wait()
        
    except RuntimeError as e:
        console.print(f"[red]❌ Error: {e}[/red]", err=True)
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ Unexpected error: {e}[/red]", err=True)
        raise typer.Exit(1)


@app.command()
def stop():
    """Stop the active capture session and generate docs."""
    try:
        session_id, pid = session.get_active_session()
        
        if not session_id:
            console.print("[red]❌ No active session running[/red]", err=True)
            raise typer.Exit(1)
        
        console.print(f"[yellow]Stopping session {session_id}...[/yellow]")
        
        session_dir = session.get_session_dir(session_id)
        
        # Kill the script process
        if pid:
            capture.kill_process_by_pid(pid)
        
        # Clear active PID
        session.clear_active_pid()
        
        # Read metadata
        metadata_file = session_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        # Parse raw to JSONL
        raw_file = session_dir / "raw.txt"
        jsonl_file = session_dir / "events.jsonl"
        
        if raw_file.exists():
            console.print("[dim]Parsing session...[/dim]")
            parser.parse_raw_to_jsonl(raw_file, jsonl_file)
        
        # Generate markdown
        console.print("[dim]Generating documentation...[/dim]")
        md_file = markdown.generate_markdown(session_id, session_dir, metadata)
        
        console.print(f"[green]✅ Session complete![/green]")
        console.print(f"[cyan]Docs saved to: {md_file}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]", err=True)
        raise typer.Exit(1)


@app.command()
def list():
    """List all captured sessions."""
    try:
        sessions = session.list_sessions()
        
        if not sessions:
            console.print("[dim]No sessions yet[/dim]")
            return
        
        table = Table(title="FixTrace Sessions")
        table.add_column("Session ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Started", style="green")
        table.add_column("Status", style="yellow")
        
        for sess in sessions:
            table.add_row(
                sess["session_id"],
                sess["name"],
                sess["started_at"][:19],
                sess["status"],
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]", err=True)
        raise typer.Exit(1)


@app.command()
def generate(session_id: str = typer.Argument(..., help="Session ID to regenerate")):
    """Regenerate markdown for a session."""
    try:
        session_dir = session.get_session_dir(session_id)
        
        if not session_dir.exists():
            console.print(f"[red]❌ Session not found: {session_id}[/red]", err=True)
            raise typer.Exit(1)
        
        metadata_file = session_dir / "metadata.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        console.print("[dim]Generating documentation...[/dim]")
        md_file = markdown.generate_markdown(session_id, session_dir, metadata)
        
        console.print(f"[green]✅ Documentation regenerated[/green]")
        console.print(f"[cyan]Saved to: {md_file}[/cyan]")
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
