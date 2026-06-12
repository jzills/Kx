from typing import Optional

import typer

from kx.commands.delete import DeleteCommand
from kx.commands.describe import DescribeCommand
from kx.commands.edit import EditCommand
from kx.commands.events import EventsCommand
from kx.commands.exec import ExecCommand
from kx.commands.get import GetCommand
from kx.commands.logs import LogsCommand
from kx.commands.port_forward import PortForwardCommand
from kx.commands.state import StateCommand
from kx.commands.tree import TreeCommand
from kx.commands.yaml import YamlCommand
from kx.events import EventsService
from kx.graph import build_indexed_tree
from kx.index import IndexService
from kx.kubectl import KubectlService
from kx.state import StateService

app = typer.Typer(help="kx - kubectl extended.")

_kubectl = KubectlService()
_state = StateService()
_events = EventsService()
_index = IndexService()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def get(
    ctx: typer.Context,
    resource: str,
    filter: Optional[str] = typer.Argument(
        None, help="Filter by name (substring match, case-insensitive)"
    ),
    namespace: str = typer.Option(None, "-n", help="Kubernetes namespace"),
):
    """List resources and assign index numbers for use with other commands."""
    command = GetCommand(kubectl=_kubectl, state=_state, index=_index)
    typer.echo(command.execute(resource, namespace, filter, ctx.args))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def describe(ctx: typer.Context, index: int):
    """Show full kubectl describe output for an indexed resource."""
    command = DescribeCommand(state=_state, kubectl=_kubectl)
    command.execute(index, ctx.args)


@app.command()
def events(index: int):
    """Show Kubernetes events for an indexed resource."""
    command = EventsCommand(state=_state, events=_events)
    typer.echo(command.execute(index))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def logs(ctx: typer.Context, index: int):
    """Stream logs for an indexed resource; aggregates across pods for Deployments, StatefulSets, DaemonSets, and Services."""
    command = LogsCommand(state=_state, kubectl=_kubectl)
    try:
        command.execute(index, ctx.args)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@app.command()
def yaml(index: int):
    """Print the raw YAML manifest for an indexed resource."""
    command = YamlCommand(state=_state, kubectl=_kubectl)
    typer.echo(command.execute(index))


@app.command()
def delete(
    index: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete an indexed resource (prompts for confirmation unless --yes)."""
    command = DeleteCommand(
        state=_state,
        kubectl=_kubectl,
        confirm=lambda msg: typer.confirm(msg, abort=True),
    )
    typer.echo(command.execute(index, yes))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def edit(ctx: typer.Context, index: int):
    """Open an indexed resource in your editor via kubectl edit."""
    command = EditCommand(state=_state, kubectl=_kubectl)
    command.execute(index, ctx.args)


@app.command(
    name="exec",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def exec_cmd(
    ctx: typer.Context,
    index: int,
    cmd: list[str] = typer.Argument(
        default=None, help="Command to run (default: bash with sh fallback)"
    ),
):
    """Open an interactive shell in an indexed pod (bash, falling back to sh)."""
    command = ExecCommand(state=_state, kubectl=_kubectl)
    try:
        command.execute(index, cmd, ctx.args)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@app.command()
def tree(
    index: int,
    indexed: bool = typer.Option(
        False, "--index", "-i", help="Assign indexes to tree nodes and update state"
    ),
):
    """Show the ownership graph for an indexed resource (deployments, statefulsets, etc.)."""
    from rich.console import Console

    command = TreeCommand(state=_state, kubectl=_kubectl, build_tree=build_indexed_tree)
    Console().print(command.execute(index, indexed))


@app.command(
    "port-forward",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def port_forward(ctx: typer.Context, index: int, port: str):
    """Port forward to the specified resource at index."""
    command = PortForwardCommand(kubectl=_kubectl, state=_state)
    try:
        command.execute(index, port, ctx.args)
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


@app.command()
def state():
    """Show the current state file."""
    command = StateCommand(state=_state)
    try:
        state = command.execute()
        typer.echo(state)
    except RuntimeError as e:
        typer.echo(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
