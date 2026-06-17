from enum import Enum

from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol

_SUPPORTED_KINDS = {Kind.Deployment, Kind.StatefulSet, Kind.DaemonSet}


class RolloutAction(str, Enum):
    status = "status"
    restart = "restart"


class RolloutCommand:
    def __init__(self, kubectl: KubectlServiceProtocol, state: StateServiceProtocol):
        self.kubectl = kubectl
        self.state = state

    def execute(self, index: int, restart: bool = False) -> str | None:
        name, namespace, kind = self.state.fields(index)
        if kind not in _SUPPORTED_KINDS:
            raise ValueError(f"rollout is not supported for '{kind}'.")
        if restart:
            self.kubectl.run(["rollout", "restart", f"{kind}/{name}", "-n", namespace])
            return f"Restarted {kind}/{name}"
        self.kubectl.run_interactive(
            ["rollout", "status", f"{kind}/{name}", "-n", namespace]
        )
        return None
