from enum import Enum

from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol

_SUPPORTED_KINDS = {Kind.Deployment, Kind.StatefulSet, Kind.DaemonSet}
_INTERACTIVE_ACTIONS = {"status"}


class RolloutAction(str, Enum):
    status = "status"
    restart = "restart"
    pause = "pause"
    resume = "resume"
    history = "history"
    undo = "undo"


class RolloutCommand:
    def __init__(self, kubectl: KubectlServiceProtocol, state: StateServiceProtocol):
        self.kubectl = kubectl
        self.state = state

    def execute(
        self, index: int, action: RolloutAction = RolloutAction.status
    ) -> str | None:
        name, namespace, kind = self.state.fields(index)
        if kind not in _SUPPORTED_KINDS:
            raise ValueError(f"rollout is not supported for '{kind}'.")
        args = ["rollout", action.value, f"{kind}/{name}", "-n", namespace]
        if action.value in _INTERACTIVE_ACTIONS:
            self.kubectl.run_interactive(args)
            return None
        return self.kubectl.run(args)
