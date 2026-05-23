import typer


def resolve_index(state, index: int) -> str:
    try:
        return state.names[index - 1]
    except IndexError:
        typer.echo("Invalid index")
        raise typer.Exit(1)

def add_indexes(output: str) -> tuple[str, list[str]]:
    import re

    lines = output.splitlines()
    if not lines:
        return output, []

    header = lines[0]
    rows = lines[1:]

    # compute column boundaries from header
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S+\s*", header)]

    headers = [header[s:e].strip() for s, e in spans]
    name_idx = headers.index("NAME")

    names = []

    parsed_rows = []
    for r in rows:
        if not r.strip():
            continue

        cols = [r[s:e].strip() for s, e in spans]

        if len(cols) <= name_idx:
            continue

        names.append(cols[name_idx])
        parsed_rows.append(cols)

    # add index column (X)
    headers = ["X"] + headers
    parsed_rows = [[str(i + 1)] + r for i, r in enumerate(parsed_rows)]

    # compute widths
    cols = list(zip(headers, *parsed_rows))
    widths = [max(len(str(cell)) for cell in col) for col in cols]

    def fmt(row):
        return "  ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))

    out = [fmt(headers)]
    out += [fmt(r) for r in parsed_rows]

    return "\n".join(out), names