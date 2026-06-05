from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class YamlCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state.fields(index)
        return self.kubectl.run(["get", kind, name, "-n", namespace, "-o", "yaml"])
