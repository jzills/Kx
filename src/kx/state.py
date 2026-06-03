from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Protocol

from kx.index import resolve_index


@dataclass
class State:
    resource_type: str
    names: list[str]
    namespace: str = "default"


class StateServiceProtocol(Protocol):
    def save(self, state: State) -> None: ...
    def load(self) -> State: ...
    def fields(self, index: int) -> tuple[str, str, str]: ...


_STATE_FILE = Path.home() / ".kx_state.json"


class StateService:
    def save(self, state: State) -> None:
        _STATE_FILE.write_text(json.dumps(asdict(state)))

    def load(self) -> State:
        if not _STATE_FILE.exists():
            raise RuntimeError("No state found. Run `kx get <resource>` first.")
        data = json.loads(_STATE_FILE.read_text())
        return State(**data)

    def fields(self, index: int) -> tuple[str, str, str]:
        state = self.load()
        name = resolve_index(state, index)
        return name, state.namespace, state.resource_type
