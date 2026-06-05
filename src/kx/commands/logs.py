from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class LogsCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int, extra_args: list[str] = []) -> None:
        name, namespace, kind = self.state.fields(index)
        if kind != Kind.Pod:
            raise ValueError("Logs are only supported on pods.")
        self.kubectl.run_interactive(["logs", name, "-n", namespace, *extra_args])
