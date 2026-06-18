from kx.state import StateHistory, StateServiceProtocol


class DropCommand:
    def __init__(self, state: StateServiceProtocol):
        self.state = state

    def execute(self, position: int) -> StateHistory:
        return self.state.drop(position)
