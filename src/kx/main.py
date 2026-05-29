import subprocess
from typing import Optional

import typer

from kx.commands.delete import DeleteCommand
from kx.commands.describe import DescribeCommand
from kx.commands.edit import EditCommand
from kx.commands.events import EventsCommand
from kx.commands.exec import ExecCommand
from kx.commands.get import GetCommand
from kx.commands.logs import LogsCommand
from kx.commands.tree import TreeCommand
from kx.commands.yaml import YamlCommand
from kx.events import filter_events, get_events, normalize_kind
from kx.graph import build_tree
from kx.kubectl import run_kubectl, run_kubectl_interactive
from kx.index import add_indexes, filter_names, resolve_index
from kx.state import save_state, load_state

app = typer.Typer(help="kx - kubectl extended.")


def _get_current_namespace() -> str:
    result = subprocess.run(
        ["kubectl", "config", "view", "--minify", "-o", "jsonpath={..namespace}"],
        capture_output=True,
        text=True,
        check=True,
    )
    ns = result.stdout.strip()
    return ns if ns else "default"


def _state_fields(index: int) -> tuple[str, str, str]:
    state = load_state()
    name = resolve_index(state, index)
    return name, state.namespace, state.resource_type


@app.command()
def get(
    resource: str,
    filter: Optional[str] = typer.Argument(None, help="Filter by name (substring match, case-insensitive)"),
    namespace: str = typer.Option(None, "-n", help="Kubernetes namespace"),
):
    """List resources and assign index numbers for use with other commands."""
    command = GetCommand(
        run_kubectl=run_kubectl,
        add_indexes=add_indexes,
        filter_names=filter_names,
        save_state=save_state,
        get_namespace=_get_current_namespace,
    )

    typer.echo(command.execute(resource, namespace, filter))


@app.command()
def describe(
    index: int,
    view: str = typer.Option("full", help="Output view: full or events"),
):
    """Show full kubectl describe output for an indexed resource."""
    command = DescribeCommand(
        state_fields=_state_fields,
        get_events=get_events,
        filter_events=filter_events,
        run_kubectl_interactive=run_kubectl_interactive,
    )

    output = command.execute(index, view)
    if output:
        typer.echo(output)


@app.command()
def events(index: int):
    """Show Kubernetes events for an indexed resource."""
    command = EventsCommand(
        state_fields=_state_fields,
        get_events=get_events,
        filter_events=filter_events,
    )

    typer.echo(command.execute(index))


@app.command()
def logs(index: int):
    """Stream logs for an indexed pod."""
    command = LogsCommand(
        state_fields=_state_fields,
        run_kubectl=run_kubectl,
    )

    try:
        typer.echo(command.execute(index))
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@app.command()
def yaml(index: int):
    """Print the raw YAML manifest for an indexed resource."""
    command = YamlCommand(
        state_fields=_state_fields,
        run_kubectl=run_kubectl,
    )

    typer.echo(command.execute(index))


@app.command()
def delete(
    index: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete an indexed resource (prompts for confirmation unless --yes)."""
    command = DeleteCommand(
        state_fields=_state_fields,
        run_kubectl=run_kubectl,
        confirm=lambda msg: typer.confirm(msg, abort=True),
    )

    typer.echo(command.execute(index, yes))


@app.command()
def edit(index: int):
    """Open an indexed resource in your editor via kubectl edit."""
    command = EditCommand(
        state_fields=_state_fields,
        run_kubectl_interactive=run_kubectl_interactive,
    )

    command.execute(index)


@app.command(name="exec")
def exec_cmd(
    index: int,
    cmd: list[str] = typer.Argument(default=None, help="Command to run (default: bash with sh fallback)"),
):
    """Open an interactive shell in an indexed pod (bash, falling back to sh)."""
    command = ExecCommand(
        state_fields=_state_fields,
        run_kubectl_interactive=run_kubectl_interactive,
    )

    try:
        command.execute(index, cmd)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@app.command()
def tree(index: int):
    """Show the ownership graph for an indexed resource (deployments, statefulsets, etc.)."""
    from rich.console import Console

    command = TreeCommand(
        state_fields=_state_fields,
        build_tree=build_tree,
        normalize_kind=normalize_kind,
    )

    Console().print(command.execute(index))


if __name__ == "__main__":
    app()
