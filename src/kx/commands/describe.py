from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class DescribeCommand:
    def __init__(
        self,
        state: StateServiceProtocol,
        kubectl: KubectlServiceProtocol,
    ):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int) -> None:
        name, namespace, kind = self.state.fields(index)
        self.kubectl.run_interactive(["describe", kind, name, "-n", namespace])
