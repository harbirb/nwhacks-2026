# Tech Stack

## Language & Framework

- Python with Typer for the CLI (fast to ship, minimal boilerplate).
- Rich for nicer terminal UX; regex/stdlib for parsing; optional pexpect for tighter process control.

## Capture Mechanism

- `script -q` to record terminal I/O; manage lifecycle via subprocess control.

## Parsing & Docs

- ANSI stripping via regex or `strip-ansi`-style helper.
- JSONL as the raw event format; markdown generation via a simple template module.

## File Layout

- Project code: `fixtrace/` package (cli.py, capture.py, session.py, parser.py, markdown.py, utils.py).
- User data: `~/.fixtrace/sessions/<session-id>.jsonl` and generated `<session-id>.md`; optional `fixtrace.db` later.

## Dependencies (MVP)

- typer, rich, pexpect, python-dateutil (or datetime only), stdlib.
