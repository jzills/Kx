from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol

_SUPPORTED_KINDS = {Kind.Deployment, Kind.StatefulSet, Kind.ReplicaSet}


class ScaleCommand:
    def __init__(self, kubectl: KubectlServiceProtocol, state: StateServiceProtocol):
        self.kubectl = kubectl
        self.state = state

    def execute(self, index: int, replicas: int) -> str:
        name, namespace, kind = self.state.fields(index)
        if kind not in _SUPPORTED_KINDS:
            raise ValueError(f"scale is not supported for '{kind}'.")
        self.kubectl.run(
            ["scale", f"{kind}/{name}", f"--replicas={replicas}", "-n", namespace]
        )
        noun = "replica" if replicas == 1 else "replicas"
        return f"Scaled {kind}/{name} to {replicas} {noun}"
