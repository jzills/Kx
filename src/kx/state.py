import json
from pathlib import Path

STATE_FILE = Path.home() / ".kx_state.json"


def save_state(resource_type: str, names: list[str], namespace: str | None):
    STATE_FILE.write_text(
        json.dumps(
            {
                "resource_type": resource_type,
                "names": names,
                "namespace": namespace,
            }
        )
    )


def load_state():
    if not STATE_FILE.exists():
        raise RuntimeError("No previous kx state found. Run `kx get` first.")

    return json.loads(STATE_FILE.read_text())