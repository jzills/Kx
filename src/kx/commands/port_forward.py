from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol

_SUPPORTED_KINDS = {"Pod", "Deployment", "ReplicaSet", "StatefulSet", "DaemonSet", "Service"}


class PortForwardCommand:
    def __init__(self, kubectl: KubectlServiceProtocol, state: StateServiceProtocol):
        self.kubectl = kubectl
        self.state = state

    def execute(self, index: int, port: str) -> None:
        name, namespace, kind = self.state.fields(index)
        canonical = self.kubectl.normalize_kind(kind)
        if canonical not in _SUPPORTED_KINDS:
            raise ValueError(f"port-forward is not supported for '{kind}'.")
        self.kubectl.run_interactive(["port-forward", f"{canonical}/{name}", port, "-n", namespace])
