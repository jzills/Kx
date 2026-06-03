from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class LogsCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state.fields(index)
        if kind != "pod":
            raise ValueError("Logs are only supported on pods.")
        return self.kubectl.run(["logs", name, "-n", namespace])
