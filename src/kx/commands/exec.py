import subprocess

from kx.kinds import Kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol

_SHELLS = ["bash", "sh"]


class ExecCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(
        self, index: int, cmd: list[str] | None, extra_args: list[str] = []
    ) -> None:
        name, namespace, kind = self.state.fields(index)
        if kind != Kind.Pod:
            raise ValueError("exec is only supported for pods.")
        if cmd:
            rc = self.kubectl.run_interactive(
                ["exec", "-it", name, "-n", namespace, *extra_args, "--", *cmd],
                stderr=subprocess.DEVNULL,
            )
            if rc != 0:
                raise ValueError(f"Command failed in container (exit {rc}).")
        else:
            for shell in _SHELLS:
                probe_rc = self.kubectl.probe(
                    [
                        "exec",
                        name,
                        "-n",
                        namespace,
                        *extra_args,
                        "--",
                        shell,
                        "-c",
                        "exit 0",
                    ]
                )
                if probe_rc == 0:
                    self.kubectl.run_interactive(
                        ["exec", "-it", name, "-n", namespace, *extra_args, "--", shell]
                    )
                    return
            raise ValueError(
                "No shell found in container. Provide an explicit command: kx exec <index> -- /path/to/binary"
            )
