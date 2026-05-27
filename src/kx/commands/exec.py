class ExecCommand:
    def __init__(self, state_fields, run_kubectl_interactive):
        self.state_fields = state_fields
        self.run_kubectl_interactive = run_kubectl_interactive

    def execute(self, index: int, cmd: list[str] | None) -> None:
        name, namespace, kind = self.state_fields(index)
        if kind.lower() not in ("pod", "pods"):
            raise ValueError("exec is only supported for pods.")
        if cmd:
            self.run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", *cmd])
        else:
            rc = self.run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", "bash"])
            if rc != 0:
                self.run_kubectl_interactive(["exec", "-it", name, "-n", namespace, "--", "sh"])
