import re
from typing import Optional

import typer
import typer.rich_utils
from typer.core import TyperCommand

from kx import console
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
from kx.graph import build_indexed_tree, build_tree
from kx.index import IndexService
from kx.kubectl import KubectlService
from kx.state import StateService


class StyledCommand(TyperCommand):
    def __init__(self, *args, **kwargs):
        kwargs.pop("rich_markup_mode", None)
        kwargs.pop("rich_help_panel", None)
        super().__init__(*args, **kwargs)

    def get_help(self, ctx: typer.Context) -> str:
        console.print_command_help(ctx)
        return ""


def _styled_error(error) -> None:
    if error.__class__.__name__ == "NoArgsIsHelpError":
        return
    msg = re.sub(r"(\bDid you mean [^\?]+\?) \1", r"\1", error.format_message())
    console.print_error(msg)


typer.rich_utils.rich_format_error = _styled_error  # type: ignore[assignment]

app = typer.Typer(
    add_help_option=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    no_color: bool = typer.Option(False, "--no-color", help="Disable styled output."),
    show_help: bool = typer.Option(
        False, "--help", is_eager=True, help="Show this message and exit."
    ),
) -> None:
    if no_color:
        console.configure(plain=True)
    if show_help or ctx.invoked_subcommand is None:
        commands = [
            (name, cmd.get_short_help_str(limit=55))
            for name, cmd in ctx.command.commands.items()
        ]
        console.print_help(commands)
        raise typer.Exit()


_kubectl = KubectlService()
_state = StateService()
_events = EventsService()
_index = IndexService()


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def get(
    ctx: typer.Context,
    resource: str,
    match: Optional[str] = typer.Option(
        None, "--match", "-m", help="Match by name (substring, case-insensitive)"
    ),
):
    """List resources and assign index numbers for use with other commands."""
    command = GetCommand(kubectl=_kubectl, state=_state, index=_index)
    try:
        result = command.execute(resource, match, ctx.args)
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)
    all_namespaces = any(arg in ("-A", "--all-namespaces") for arg in ctx.args)
    if all_namespaces:
        namespace = "all namespaces"
    else:
        try:
            namespace = _state.load().namespace
        except RuntimeError:
            namespace = "default"
    console.render_indexed_table(result, resource, namespace)


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def describe(ctx: typer.Context, index: int):
    """Show full kubectl describe output for an indexed resource."""
    name, _ns, kind = _state.fields(index)
    console.print_banner(kind, name)
    command = DescribeCommand(state=_state, kubectl=_kubectl)
    command.execute(index, ctx.args)


@app.command(cls=StyledCommand)
def events(index: int):
    """Show Kubernetes events for an indexed resource."""
    command = EventsCommand(state=_state, events=_events)
    console.render_events_table(command.execute(index))


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def logs(ctx: typer.Context, index: int):
    """Stream logs for an indexed resource; aggregates across pods for Deployments, StatefulSets, DaemonSets, and Services."""
    name, _ns, kind = _state.fields(index)
    console.print_banner(kind, name)
    command = LogsCommand(state=_state, kubectl=_kubectl)
    try:
        command.execute(index, ctx.args)
    except (ValueError, RuntimeError) as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def yaml(index: int):
    """Print the raw YAML manifest for an indexed resource."""
    command = YamlCommand(state=_state, kubectl=_kubectl)
    try:
        console.print_raw(command.execute(index))
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
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
    try:
        console.print_success(command.execute(index, yes))
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def edit(ctx: typer.Context, index: int):
    """Open an indexed resource in your editor via kubectl edit."""
    name, _ns, kind = _state.fields(index)
    console.print_banner(kind, name)
    command = EditCommand(state=_state, kubectl=_kubectl)
    command.execute(index, ctx.args)


@app.command(
    name="exec",
    cls=StyledCommand,
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
    name, _ns, kind = _state.fields(index)
    console.print_banner(kind, name)
    command = ExecCommand(state=_state, kubectl=_kubectl)
    try:
        command.execute(index, cmd, ctx.args)
    except ValueError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def tree(
    index: int,
    indexed: bool = typer.Option(
        False, "--index", "-i", help="Assign indexes to tree nodes and update state"
    ),
):
    """Show the ownership graph for an indexed resource (deployments, statefulsets, etc.)."""
    command = TreeCommand(
        state=_state,
        kubectl=_kubectl,
        build_tree=build_tree,
        build_indexed_tree=build_indexed_tree,
    )
    console.print_rich(command.execute(index, indexed))


@app.command(
    "port-forward",
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def port_forward(ctx: typer.Context, index: int, port: str):
    """Port forward to the specified resource at index."""
    name, _ns, kind = _state.fields(index)
    console.print_banner(kind, name, extra=port)
    command = PortForwardCommand(kubectl=_kubectl, state=_state)
    try:
        command.execute(index, port, ctx.args)
    except ValueError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def state():
    """Show the current state file."""
    command = StateCommand(state=_state)
    try:
        console.render_state(command.execute())
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
