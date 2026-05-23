import subprocess

import typer

from kx.kubectl import run_kubectl, run_kubectl_interactive
from kx.index import add_indexes, resolve_index
from kx.state import KxState, save_state, load_state

app = typer.Typer(help="kx - kubectl extended with indexing")


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
    namespace: str = typer.Option(None, "-n", help="Kubernetes namespace"),
):
    """List resources and assign index numbers for use with other commands."""
    if namespace is None:
        namespace = _get_current_namespace()

    output = run_kubectl(["get", resource, "-n", namespace])
    indexed_output, names = add_indexes(output)
    typer.echo(indexed_output)
    save_state(KxState(resource_type=resource, names=names, namespace=namespace))


@app.command()
def describe(
    index: int,
    view: str = typer.Option("full", help="Output view: full or events"),
):
    """Show full kubectl describe output for an indexed resource."""
    name, namespace, kind = _state_fields(index)

    if view == "events":
        from kx.events import get_events, filter_events

        all_events = get_events(namespace)
        events = filter_events(all_events, name, kind)

        if not events:
            typer.echo("No events found")
            return

        for e in events:
            obj = e.involved_object
            typer.echo(
                f"{e.type:8} {e.reason:30} "
                f"{obj.kind:10} {e.metadata.creation_timestamp} "
                f"{e.message}"
            )
        return

    subprocess.run(["kubectl", "describe", kind, name, "-n", namespace])


@app.command()
def events(index: int):
    """Show Kubernetes events for an indexed resource."""
    from kx.events import get_events, filter_events

    name, namespace, kind = _state_fields(index)
    all_events = get_events(namespace)
    filtered = filter_events(all_events, name, kind)

    if not filtered:
        typer.echo("No events found")
        return

    for e in filtered:
        obj = e.involved_object
        typer.echo(
            f"{e.type:8} {e.reason:30} "
            f"{obj.kind:10} {e.metadata.creation_timestamp} "
            f"{e.message}"
        )


@app.command()
def logs(index: int):
    """Stream logs for an indexed pod."""
    name, namespace, kind = _state_fields(index)

    if kind != "pod":
        typer.echo("Logs are only supported on pods.")
        raise typer.Exit(1)

    args = ["logs", name, "-n", namespace]
    typer.echo(run_kubectl(args))


@app.command()
def yaml(index: int):
    """Print the raw YAML manifest for an indexed resource."""
    name, namespace, kind = _state_fields(index)
    typer.echo(run_kubectl(["get", kind, name, "-n", namespace, "-o", "yaml"]))


@app.command()
def delete(
    index: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete an indexed resource (prompts for confirmation unless --yes)."""
    name, namespace, kind = _state_fields(index)
    if not yes:
        typer.confirm(f"Delete {kind}/{name} in {namespace}?", abort=True)
    run_kubectl(["delete", kind, name, "-n", namespace])
    typer.echo(f"Deleted {kind}/{name}")


@app.command()
def edit(index: int):
    """Open an indexed resource in your editor via kubectl edit."""
    name, namespace, kind = _state_fields(index)
    run_kubectl_interactive(["edit", kind, name, "-n", namespace])


@app.command(name="exec")
def exec_cmd(
    index: int,
    cmd: list[str] = typer.Argument(default=None, help="Command to run (default: bash with sh fallback)"),
):
    """Open an interactive shell in an indexed pod (bash, falling back to sh)."""
    name, namespace, kind = _state_fields(index)
    if kind.lower() not in ("pod", "pods"):
        typer.echo("exec is only supported for pods.")
        raise typer.Exit(1)
    if cmd:
        run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", *cmd])
    else:
        rc = run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", "bash"])
        if rc != 0:
            run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", "sh"])


@app.command()
def tree(index: int):
    """Show the ownership graph for an indexed resource (deployments, statefulsets, etc.)."""
    from kx.events import normalize_kind
    from kx.graph import build_tree
    from rich.console import Console

    name, namespace, kind = _state_fields(index)
    Console().print(build_tree(normalize_kind(kind), name, namespace))


if __name__ == "__main__":
    app()
