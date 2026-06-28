from dataclasses import asdict
import json

from kx.state import StateServiceProtocol


class BackCommand:
    def __init__(self, state: StateServiceProtocol):
        self.state = state

    def execute(self) -> str:
        state = self.state.navigate(-1)
        return json.dumps(asdict(state), indent=2)
