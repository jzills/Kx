import re
from typing import TYPE_CHECKING, Protocol

import typer

if TYPE_CHECKING:
    from kx.state import State


def resolve_index(state, index: int) -> str:
    if index < 1:
        typer.echo("Invalid index")
        raise typer.Exit(1)
    try:
        return state.names[index - 1]
    except IndexError:
        typer.echo("Invalid index")
        raise typer.Exit(1)


def _parse_output(output: str) -> tuple[list[str], list[list[str]], int]:
    lines = output.splitlines()
    if not lines:
        return [], [], 0

    header = lines[0]
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+\s*", header)]
    headers = [header[s:e].strip() for s, e in spans]
    if "NAME" not in headers:
        return [], [], 0
    name_idx = headers.index("NAME")

    rows = []
    for r in lines[1:]:
        if not r.strip():
            continue
        cols = [r[s:e].strip() for s, e in spans]
        if len(cols) <= name_idx:
            continue
        rows.append(cols)

    return headers, rows, name_idx


class IndexServiceProtocol(Protocol):
    def add(self, output: str) -> tuple[str, list[str]]: ...
    def filter(self, output: str, term: str) -> str: ...
    def resolve(self, state: "State", index: int) -> str: ...


class IndexService:
    def add(self, output: str) -> tuple[str, list[str]]:
        headers, rows, name_idx = _parse_output(output)
        if not headers:
            return output, []

        names = [r[name_idx] for r in rows]

        headers = ["X"] + headers
        rows = [[str(i + 1)] + r for i, r in enumerate(rows)]

        all_rows = [headers] + rows
        cols = list(zip(*all_rows))
        widths = [max(len(cell) for cell in col) for col in cols]

        def fmt(row: list[str]) -> str:
            return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

        return "\n".join(fmt(r) for r in all_rows), names

    def filter(self, output: str, term: str) -> str:
        headers, rows, name_idx = _parse_output(output)
        if not headers:
            return output

        filtered = [r for r in rows if term.lower() in r[name_idx].lower()]

        all_rows = [headers] + filtered
        if len(all_rows) == 1:
            return output.splitlines()[0]

        cols = list(zip(*all_rows))
        widths = [max(len(cell) for cell in col) for col in cols]

        def fmt(row: list[str]) -> str:
            return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

        return "\n".join(fmt(r) for r in all_rows)

    def resolve(self, state: "State", index: int) -> str:
        return resolve_index(state, index)
