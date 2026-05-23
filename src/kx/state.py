from dataclasses import dataclass, asdict
import json
from pathlib import Path

STATE_FILE = Path.home() / ".kx_state.json"


@dataclass
class KxState:
    resource_type: str
    names: list[str]
    namespace: str = "default"


def save_state(state: KxState) -> None:
    STATE_FILE.write_text(json.dumps(asdict(state)))


def load_state() -> KxState:
    if not STATE_FILE.exists():
        raise RuntimeError("No state found. Run `kx get <resource>` first.")
    data = json.loads(STATE_FILE.read_text())
    return KxState(**data)
