class LogsCommand:
    def __init__(self, state_fields, run_kubectl):
        self.state_fields = state_fields
        self.run_kubectl = run_kubectl

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state_fields(index)
        if kind != "pod":
            raise ValueError("Logs are only supported on pods.")
        return self.run_kubectl(["logs", name, "-n", namespace])
