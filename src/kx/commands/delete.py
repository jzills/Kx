from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol
from kx.types import Confirm


class DeleteCommand:
    def __init__(
        self,
        state: StateServiceProtocol,
        kubectl: KubectlServiceProtocol,
        confirm: Confirm,
    ):
        self.state = state
        self.kubectl = kubectl
        self.confirm = confirm

    def execute(self, index: int, yes: bool) -> str:
        name, namespace, kind = self.state.fields(index)
        if not yes:
            self.confirm(f"Delete {kind}/{name} in {namespace}?")
        self.kubectl.run(["delete", kind, name, "-n", namespace])
        return f"Deleted {kind}/{name}"
