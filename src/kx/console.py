import re
import json

from rich.console import Console
from rich.table import Table

from kx.kinds import plural_display

COLOR_HEADER = "#3fb950"
COLOR_DIM = "#7d8590"
COLOR_BODY = "#e6edf3"
COLOR_ERROR = "#f85149"
COLOR_WARNING = "#e3b341"

_STATUS_GREEN = {
    "Running",
    "Active",
    "Bound",
    "Available",
    "Healthy",
    "Completed",
    "Succeeded",
}
_STATUS_YELLOW = {"Pending", "Terminating", "Unknown"}
_STATUS_RED = {
    "Error",
    "CrashLoopBackOff",
    "OOMKilled",
    "Failed",
    "Evicted",
    "ImagePullBackOff",
    "ErrImagePull",
    "InvalidImageName",
}

_console = Console()


def configure(plain: bool) -> None:
    global _console
    _console = Console(no_color=True, highlight=False) if plain else Console()


def print_success(msg: str) -> None:
    _console.print(f"[bold {COLOR_HEADER}]✓[/bold {COLOR_HEADER}] {msg}")


def print_error(msg: str) -> None:
    styled = re.sub(r"'([^']+)'", f"[{COLOR_HEADER}]'\\1'[/{COLOR_HEADER}]", msg)
    _console.print(
        f"[bold {COLOR_HEADER}]✗[/bold {COLOR_HEADER}] [{COLOR_BODY}]{styled}[/{COLOR_BODY}]"
    )


def print_banner(kind: str, name: str, extra: str = "") -> None:
    suffix = f" {extra}" if extra else ""
    _console.print(f"[{COLOR_DIM}]→ {kind}/{name}{suffix}[/{COLOR_DIM}]")


def print_raw(text: str) -> None:
    _console.print(text, markup=False, highlight=False)


def print_rich(renderable) -> None:
    _console.print(renderable)


def _status_color(status: str) -> str:
    if status in _STATUS_GREEN:
        return COLOR_HEADER
    if status in _STATUS_RED:
        return COLOR_ERROR
    if status in _STATUS_YELLOW or "Init" in status or status == "ContainerCreating":
        return COLOR_WARNING
    return COLOR_BODY


def render_indexed_table(text: str, resource_type: str, namespace: str) -> None:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return

    header_line = lines[0]
    first_col = header_line.split()[0] if header_line.split() else ""
    if first_col != "X":
        _console.print(text, markup=False, highlight=False)
        return

    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+\s*", header_line)]
    headers = [header_line[start:end].strip() for start, end in spans]

    rows = []
    for line in lines[1:]:
        cols = [line[start:end].strip() for start, end in spans]
        if cols:
            rows.append(cols)

    restarts_col = headers.index("RESTARTS") if "RESTARTS" in headers else -1
    if restarts_col >= 0:
        max_num_width = max(
            (
                len(m.group(1))
                for row in rows
                if restarts_col < len(row)
                for m in [re.match(r"(\d+)", row[restarts_col])]
                if m
            ),
            default=0,
        )
        if max_num_width:
            rows = [
                [
                    re.sub(r"^(\d+)", lambda m: m.group(1).rjust(max_num_width), cell)
                    if col_idx == restarts_col
                    else cell
                    for col_idx, cell in enumerate(row)
                ]
                for row in rows
            ]

    table = Table(
        show_header=True,
        header_style=f"bold {COLOR_HEADER}",
        box=None,
        padding=(0, 2),
    )
    _right_aligned = {"X", "AGE"}
    for header in headers:
        table.add_column(
            header, justify="right" if header in _right_aligned else "left"
        )

    status_col = headers.index("STATUS") if "STATUS" in headers else -1

    for row in rows:
        styled = []
        for index, cell in enumerate(row):
            if index == status_col:
                styled.append(f"[{_status_color(cell)}]{cell}[/]")
            else:
                styled.append(cell)
        table.add_row(*styled)

    count = len(rows)
    label = "item" if count == 1 else "items"
    _console.print(
        f"[{COLOR_DIM}]{plural_display(resource_type)} · {namespace} · {count} {label}[/{COLOR_DIM}]"
    )
    _console.print(table)


def render_events_table(text: str) -> None:
    if text.strip() == "No events found":
        _console.print(f"[{COLOR_DIM}]No events found[/{COLOR_DIM}]")
        return

    table = Table(
        show_header=True,
        header_style=f"bold {COLOR_HEADER}",
        box=None,
        padding=(0, 2),
    )
    for col in ("TYPE", "REASON", "KIND", "TIMESTAMP", "MESSAGE"):
        table.add_column(col)

    for line in text.splitlines():
        if not line.strip():
            continue
        event_type = line[0:8].strip()
        reason = line[9:39].strip()
        kind = line[40:50].strip()
        rest = line[51:]
        parts = rest.split(" ", 2)
        timestamp = (
            f"{parts[0]} {parts[1]}" if len(parts) >= 2 else (parts[0] if parts else "")
        )
        message = parts[2] if len(parts) >= 3 else ""

        type_color = COLOR_DIM if event_type == "Normal" else COLOR_WARNING
        table.add_row(
            f"[{type_color}]{event_type}[/]",
            reason,
            kind,
            f"[{COLOR_DIM}]{timestamp}[/]",
            message,
        )

    _console.print(table)


def print_command_help(ctx) -> None:
    import click as _click

    cmd = ctx.command
    _console.print()
    _console.print(f"[bold {COLOR_HEADER}]{ctx.command_path}[/bold {COLOR_HEADER}]")
    if cmd.help:
        _console.print(f"[{COLOR_DIM}]{cmd.help}[/{COLOR_DIM}]")
    _console.print()
    _console.rule(style=COLOR_DIM)
    _console.print()

    args = [p for p in cmd.params if isinstance(p, _click.Argument)]
    opts = [
        p for p in cmd.params if isinstance(p, _click.Option) and "--help" not in p.opts
    ]

    args_str = " ".join(p.human_readable_name for p in args)
    usage = f"{ctx.command_path} [OPTIONS]"
    if args_str:
        usage += f" {args_str}"
    _console.print(f"[{COLOR_DIM}]Usage[/{COLOR_DIM}]  {usage}", highlight=False)

    if args:
        _console.print()
        _console.print(f"[bold {COLOR_HEADER}]Arguments[/bold {COLOR_HEADER}]")
        for arg in args:
            label = "required" if arg.required else "optional"
            _console.print(
                f"  [{COLOR_BODY}]{arg.human_readable_name:<16}[/{COLOR_BODY}]  [{COLOR_DIM}]{label}[/{COLOR_DIM}]"
            )

    _console.print()
    _console.print(f"[bold {COLOR_HEADER}]Options[/bold {COLOR_HEADER}]")
    for opt in opts:
        names = "  ".join(opt.opts)
        _console.print(
            f"  [{COLOR_BODY}]{names:<20}[/{COLOR_BODY}]  [{COLOR_DIM}]{opt.help or ''}[/{COLOR_DIM}]"
        )
    _console.print(
        f"  [{COLOR_BODY}]{'--help':<20}[/{COLOR_BODY}]  [{COLOR_DIM}]Show this message and exit.[/{COLOR_DIM}]"
    )


_KX_ART = [
    "██╗  ██╗██╗  ██╗",
    "██║ ██╔╝╚██╗██╔╝",
    "█████╔╝  ╚███╔╝ ",
    "██╔═██╗  ██╔██╗ ",
    "██║  ██╗██╔╝ ██╗",
    "╚═╝  ╚═╝╚═╝  ╚═╝",
]


def print_help(commands: list[tuple[str, str]]) -> None:
    _console.print()
    for line in _KX_ART:
        _console.print(f"[bold {COLOR_HEADER}]{line}[/bold {COLOR_HEADER}]")
    _console.print(f"[{COLOR_DIM}]kubectl, indexed.[/{COLOR_DIM}]")
    _console.print()
    _console.rule(style=COLOR_DIM)
    _console.print()
    _console.print(
        f"[{COLOR_DIM}]Usage[/{COLOR_DIM}]  kx [OPTIONS] COMMAND [ARGS]...",
        highlight=False,
    )
    _console.print()
    _console.print(f"[bold {COLOR_HEADER}]Commands[/bold {COLOR_HEADER}]")
    for name, doc in commands:
        _console.print(
            f"  [{COLOR_BODY}]{name:<14}[/{COLOR_BODY}]  [{COLOR_DIM}]{doc}[/{COLOR_DIM}]"
        )
    _console.print()
    _console.print(f"[bold {COLOR_HEADER}]Options[/bold {COLOR_HEADER}]")
    _console.print(
        f"  [{COLOR_BODY}]{'--no-color':<14}[/{COLOR_BODY}]  [{COLOR_DIM}]Disable styled output.[/{COLOR_DIM}]"
    )
    _console.print(
        f"  [{COLOR_BODY}]{'--help':<14}[/{COLOR_BODY}]  [{COLOR_DIM}]Show this message and exit.[/{COLOR_DIM}]"
    )


def render_state(json_str: str) -> None:
    data = json.loads(json_str)
    namespace = data.get("namespace", "default")
    resources = data.get("resources", {})
    _console.print(f"[{COLOR_DIM}]namespace:[/{COLOR_DIM}] {namespace}")
    for index, (name, kind) in enumerate(resources.items(), start=1):
        _console.print(
            f"  [{COLOR_DIM}]{index}[/{COLOR_DIM}]  [{COLOR_HEADER}]{kind}[/{COLOR_HEADER}] {name}"
        )
