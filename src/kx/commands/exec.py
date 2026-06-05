from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class ExecCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int, cmd: list[str] | None, extra_args: list[str] = []) -> None:
        name, namespace, kind = self.state.fields(index)
        if kind != Kind.Pod:
            raise ValueError("exec is only supported for pods.")
        if cmd:
            self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, *extra_args, "--", *cmd])
        else:
            rc = self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, *extra_args, "--", "bash"])
            if rc != 0:
                self.kubectl.run_interactive(["exec", "-it", name, "-n", namespace, *extra_args, "--", "sh"])
