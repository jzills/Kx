# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Python 3.12, virtual environment at `.venv/`.

Activate before running anything:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Stack

- **[Typer](https://typer.tiangolo.com/)** — CLI framework built on Click, with type-hint-driven argument/option parsing and auto-generated help text.
- **Rich** — installed as a typer dependency; available for terminal formatting.

## Running the CLI

Once a main entry point exists (e.g. `main.py`):
```bash
python main.py --help
python main.py <command> [args]
```
