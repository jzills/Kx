# kx Rich Console — Design Spec

**Date:** 2026-06-12
**Branch:** `feat/rich-console`

## Context

kx has solid baseline functionality but all terminal output is plain text — no color, no structure beyond manual column alignment, and no visual identity. The goal is to give kx the polished feel of modern Kubernetes tooling (stern, kubectx, helm) while keeping output clean, pipeable, and opt-out friendly.

---

## Visual Style

**Palette (dark-terminal optimized, GitHub dark-inspired):**

| Role | Color |
|---|---|
| Column headers / success | `#3fb950` (green) |
| Metadata / dim text | `#7d8590` (gray) |
| Body text | `#e6edf3` (near-white) |
| Separator lines | `#21262d` (dark gray) |
| Errors | `#f85149` (red) |
| Warnings / Pending status | `#e3b341` (yellow) |

**Get output structure:**
```
PODS · default · 4 items        ← dim metadata header
  #   NAME                  READY   STATUS      AGE    ← bold green header row
  1   api-deployment-x2k9p   1/1     Running     2d    ← body, status colored
  2   worker-7d9f4b-p3mn2    0/1     CrashLoop   5m
```

**Help header:**
```
kx                              ← bold green, large
kubectl, with indexes.          ← dim tagline
────────────────────────────    ← separator
Usage: kx [OPTIONS] COMMAND...
```

---

## Architecture

### New: `src/kx/console.py`

Single module owning all presentation. Contains:

- A module-level `Console` instance (Rich)
- `configure(plain: bool)` — called once at startup; replaces the Console with `Console(no_color=True, highlight=False)` when `plain=True`
- Output helpers:
  - `print_success(msg)` — green `✓ msg`
  - `print_error(msg)` — red `✗ msg`
  - `print_banner(kind, name)` — dim `→ kind/name` prefix before kubectl passthroughs
  - `render_indexed_table(text, resource_type, namespace)` — parses IndexService string output into a Rich Table with colored STATUS column and dim metadata header
  - `render_events_table(text)` — same for events, coloring TYPE and REASON columns
  - `render_state(state)` — compact formatted summary replacing raw JSON

### Modified: `src/kx/main.py`

- Add `app = typer.Typer(rich_markup_mode="rich", ...)` with a Rich markup `help=` string that embeds the styled `kx` + tagline + separator directly — no separate function needed
- Add `@app.callback()` with a global `--no-color` flag that calls `console.configure(plain=True)`
- Replace `typer.echo(result)` calls with appropriate `console.*` helpers per command
- Add `console.print_banner(kind, name)` before each `run_kubectl_interactive()` call

### Unchanged

All command classes (`src/kx/commands/`), `IndexService`, `EventsService`, `StateService`, `KubectlService` — no changes. Commands still return strings/data; only `main.py`'s output layer changes.

---

## Per-Command Output

| Command | Output type | Treatment |
|---|---|---|
| `kx get` | indexed table | `render_indexed_table()` |
| `kx events` | events table | `render_events_table()` |
| `kx delete` | result string | `print_success()` |
| `kx state` | JSON | `render_state()` |
| `kx tree` | Rich Tree | keep as-is; use shared Console instance |
| `kx describe` | kubectl passthrough | `print_banner()` before stream |
| `kx logs` | kubectl passthrough | `print_banner()` before stream |
| `kx exec` | kubectl passthrough | `print_banner()` before stream |
| `kx edit` | kubectl passthrough | `print_banner()` before stream |
| `kx port-forward` | kubectl passthrough | `print_banner()` before stream |
| errors | plain Typer errors | `print_error()` |
| `--help` | Typer default | styled header via `rich_markup_mode` |

### Status color rules (for `render_indexed_table`)

- Green: `Running`, `Active`, `Bound`, `Available`, `Healthy`
- Yellow: `Pending`, `Terminating`, `Unknown`, `Init`
- Red: `Error`, `CrashLoopBackOff`, `OOMKilled`, `Failed`, `Evicted`, `ImagePullBackOff`, `ErrImagePull`
- Default: everything else

---

## `--no-color` Flag

Global option on the app callback. Per-invocation only — no persistent state.

```
kx --no-color get pods
```

Calls `console.configure(plain=True)` before any command runs. Strips all ANSI output including bold/dim, not just colors.

Users can also set `NO_COLOR=1` in their shell profile for a permanent opt-out (Rich respects this automatically without any code changes on our end).

---

## Compatibility Notes

- `Console` is created without `force_terminal=True` so Rich's automatic TTY detection works — piped output strips ANSI codes naturally
- `NO_COLOR` env var is respected automatically by Rich
- `TERM=dumb` is respected automatically by Rich
- Unicode block characters (`█`) are avoided; all art uses plain ASCII

---

## Verification

```bash
# Styled output
kx get pods
kx get deployments
kx events 1
kx describe 1
kx delete 1
kx --help

# Plain output
kx --no-color get pods
NO_COLOR=1 kx get pods

# Piped output (should have no ANSI codes)
kx get pods | cat
kx get pods | grep Running
```

Visually confirm:
- Status column colors (green/yellow/red)
- Dim metadata header above table
- Bold green column headers
- Banner line before passthrough commands
- Clean plain text with `--no-color`
- No escape codes in piped output
