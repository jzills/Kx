import re
from typing import Optional

import typer
import typer.rich_utils
from typer.core import TyperCommand

from kx import console
from kx.commands.delete import DeleteCommand
from kx.commands.labels import LabelsCommand
from kx.commands.describe import DescribeCommand
from kx.commands.edit import EditCommand
from kx.commands.events import EventsCommand
from kx.commands.exec import ExecCommand
from kx.commands.get import GetCommand
from kx.commands.logs import LogsCommand
from kx.commands.port_forward import PortForwardCommand
from kx.commands.namespace import NamespaceCommand
from kx.commands.rollout import RolloutAction, RolloutCommand
from kx.commands.scale import ScaleCommand
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
            if not cmd.hidden
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
def describe(ctx: typer.Context, indexes: list[int]):
    """Show full kubectl describe output for one or more indexed resources."""
    command = DescribeCommand(state=_state, kubectl=_kubectl)
    for index in indexes:
        name, ns, kind = _state.fields(index)
        console.print_banner(kind, name, namespace=ns)
        command.execute(index, ctx.args)


@app.command(cls=StyledCommand)
def events(indexes: list[int]):
    """Show Kubernetes events for one or more indexed resources."""
    command = EventsCommand(state=_state, events=_events)
    for index in indexes:
        name, ns, kind = _state.fields(index)
        result = command.execute(index)
        if result.strip() == "No events found":
            count = 0
        else:
            count = len([line for line in result.splitlines() if line.strip()])
        extra = f"{count} {'item' if count == 1 else 'items'}" if count else ""
        console.print_banner(kind, name, namespace=ns, extra=extra)
        console.render_events_table(result)


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def logs(ctx: typer.Context, index: int):
    """Stream logs for an indexed resource; aggregates across pods for Deployments, StatefulSets, DaemonSets, and Services."""
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
    command = LogsCommand(state=_state, kubectl=_kubectl)
    try:
        command.execute(index, ctx.args)
    except (ValueError, RuntimeError) as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def labels(
    index: int,
    selector: bool = typer.Option(
        False, "--selector", "-s", help="Output as a copy-pastable label selector"
    ),
):
    """Show labels for an indexed resource."""
    command = LabelsCommand(state=_state, kubectl=_kubectl)
    try:
        label_map = command.execute(index)
    except typer.Exit:
        raise
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)
    name, ns, kind = _state.fields(index)
    count = len(label_map)
    extra = f"{count} {'item' if count == 1 else 'items'}"
    console.print_banner(kind, name, namespace=ns, extra=extra)
    if selector:
        console.print_raw(
            ",".join(f"{key}={value}" for key, value in label_map.items())
        )
    else:
        console.render_labels(label_map)


@app.command(cls=StyledCommand)
def yaml(
    index: int,
    show: Optional[str] = typer.Option(
        None,
        "--show",
        help="Comma-separated top-level YAML fields to display (e.g. metadata,spec)",
    ),
):
    """Print the raw YAML manifest for an indexed resource."""
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
    command = YamlCommand(state=_state, kubectl=_kubectl)
    try:
        fields = [field.strip() for field in show.split(",")] if show else None
        console.print_raw(command.execute(index, fields))
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def delete(
    indexes: list[int],
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete one or more indexed resources (prompts for confirmation unless --yes)."""
    command = DeleteCommand(
        state=_state,
        kubectl=_kubectl,
        confirm=lambda msg: typer.confirm(msg, abort=True),
    )
    for index in indexes:
        try:
            console.print_success(command.execute(index, yes))
        except typer.Exit:
            raise
        except RuntimeError as e:
            console.print_error(str(e))
            raise typer.Exit(1)


@app.command(
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def edit(ctx: typer.Context, index: int):
    """Open an indexed resource in your editor via kubectl edit."""
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
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
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
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
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
    command = TreeCommand(
        state=_state,
        kubectl=_kubectl,
        build_tree=build_tree,
        build_indexed_tree=build_indexed_tree,
    )
    console.print_rich(command.execute(index, indexed))


@app.command(cls=StyledCommand)
def rollout(action: RolloutAction, index: int):
    """Show rollout status or restart an indexed Deployment, StatefulSet, or DaemonSet."""
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns)
    command = RolloutCommand(kubectl=_kubectl, state=_state)
    try:
        result = command.execute(index, restart=(action == RolloutAction.restart))
        if result:
            console.print_success(result)
    except ValueError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def scale(index: int, replicas: int):
    """Scale an indexed Deployment, StatefulSet, or ReplicaSet to a given replica count."""
    command = ScaleCommand(kubectl=_kubectl, state=_state)
    try:
        console.print_success(command.execute(index, replicas))
    except ValueError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(
    "port-forward",
    cls=StyledCommand,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def port_forward(ctx: typer.Context, index: int, port: str):
    """Port forward to the specified resource at index."""
    name, ns, kind = _state.fields(index)
    console.print_banner(kind, name, namespace=ns, extra=port)
    command = PortForwardCommand(kubectl=_kubectl, state=_state)
    try:
        command.execute(index, port, ctx.args)
    except ValueError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


@app.command(cls=StyledCommand)
def namespace(index: int):
    """Switch to an indexed namespace (run kx get namespaces first)."""
    command = NamespaceCommand(state=_state, kubectl=_kubectl)
    try:
        console.print_success(f"Switched to '{command.execute(index)}'")
    except RuntimeError as e:
        console.print_error(str(e))
        raise typer.Exit(1)


namespace._aliases = ["ns"]


@app.command(name="ns", cls=StyledCommand, hidden=True)
def namespace_alias(index: int):
    """Alias for namespace."""
    command = NamespaceCommand(state=_state, kubectl=_kubectl)
    try:
        console.print_success(f"Switched to '{command.execute(index)}'")
    except RuntimeError as e:
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
