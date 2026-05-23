import subprocess

import typer

from kx.kubectl import run_kubectl
from kx.index import add_indexes, resolve_index
from kx.state import save_state, load_state

app = typer.Typer(help="kx - kubectl extended with indexing")


def get_current_namespace() -> str:
    result = subprocess.run(
        ["kubectl", "config", "view", "--minify", "-o",
         "jsonpath={..namespace}"],
        capture_output=True,
        text=True,
        check=True,
    )

    ns = result.stdout.strip()
    return ns if ns else "default"

@app.command()
def get(
    resource: str,
    namespace: str = typer.Option(None, "-n", help="Kubernetes namespace"),
):
    args = ["get", resource]

    if namespace is None:
        namespace = get_current_namespace()

    output = run_kubectl(args)

    indexed_output, names = add_indexes(output)

    typer.echo(indexed_output)

    save_state(resource, names, namespace)


@app.command()
def describe(index: int, view: str = "full"):
    state = load_state()

    name = state["names"][index - 1]
    namespace = state.get("namespace", "default")
    kind = state["resource_type"]

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

    subprocess.run([
        "kubectl", "describe", kind, name, "-n", namespace
    ])

@app.command()
def events(index: int):
    from kx.events import get_events, filter_events

    state = load_state()

    name = state["names"][index - 1]
    namespace = state.get("namespace", "default")
    kind = state["resource_type"]

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
    state = load_state()

    if state["resource_type"] != "pod":
        typer.echo("Logs are only supported on pods.")
        raise typer.Exit(1)

    name = resolve_index(state, index)
    
    args = ["logs", name]

    if state.get("namespace"):
        args += ["-n", state["namespace"]]

    output = run_kubectl(args)
    typer.echo(output)

if __name__ == "__main__":
    app()