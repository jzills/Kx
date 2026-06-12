from dataclasses import asdict
import json

from kx.state import State, StateServiceProtocol


class StateCommand:
    def __init__(self, state: StateServiceProtocol):
        self.state = state

    def execute(self) -> State:
        state = self.state.load()
        return json.dumps(asdict(state), indent=2)
