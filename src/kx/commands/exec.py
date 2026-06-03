from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class ExecCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int, cmd: list[str] | None) -> None:
        name, namespace, kind = self.state.fields(index)
        if self.kubectl.normalize_kind(kind) != Kind.Pod:
            raise ValueError("exec is only supported for pods.")
        if cmd:
            self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, "--", *cmd])
        else:
            rc = self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, "--", "bash"])
            if rc != 0:
                self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, "--", "sh"])
