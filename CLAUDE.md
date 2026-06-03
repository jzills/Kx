# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

Python 3.12, virtual environment at `.venv/`.

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the CLI

```bash
python -m kx.main --help
python -m kx.main <command> [args]
```

After installing (`pip install -e .`), the `kx` entrypoint is available directly.

## Linting

```bash
ruff check src/
```

## Stack

- **Typer** — CLI framework; commands defined in `main.py` with injected dependencies
- **kubernetes** — Python SDK used in `events.py`, `graph.py`, `k8s.py` for live cluster calls
- **Rich** — used in `graph.py` for `Tree` rendering; available elsewhere

## Architecture

`kx` is a kubectl wrapper adding index-based resource selection. The workflow: `kx get <resource>` lists resources and saves state; all other commands resolve a numeric index back to a resource name from that saved state.

**State flow:** `kx get` → `kubectl get` output → `IndexService.add()` parses the NAME column and assigns 1-based indexes → `State` (resource_type, names, namespace) is persisted to `~/.kx_state.json` via `StateService.save()` → subsequent commands call `StateService.fields(index)` which loads state and resolves the name.

**Command pattern:** Each command in `src/kx/commands/` is a class injected with callables (`run_kubectl`, `save_state`, `get_events`, etc.) in `main.py`. This keeps commands testable without subprocess or filesystem side-effects. Commands receive only plain functions, not the module-level implementations.

**Two kubectl wrappers:**
- `run_kubectl(args)` — captures stdout, returns string (used for `get`, `logs`, `yaml`, `delete`)
- `run_kubectl_interactive(args)` — streams stdio through to the terminal (used for `describe`, `exec`, `edit`)

**Kubernetes SDK usage** (`events.py`, `graph.py`): `load_k8s()` in `k8s.py` tries `load_kube_config()` then falls back to `load_incluster_config()`. The `tree` command uses the Python SDK directly (not kubectl) to walk ownership references across Deployment → ReplicaSet → Pod → Container.

**`normalize_kind()`** in `events.py` maps kubectl shorthand (e.g. `pods`, `deploy`, `svc`) to canonical Kubernetes kind names used in event `involved_object.kind` comparisons.

## Release

Releases are triggered by pushing a `release/vX.Y.Z` branch. CI extracts the version, stamps `pyproject.toml`, builds, publishes to PyPI, and opens a PR back to `main`.
