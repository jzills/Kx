class YamlCommand:
    def __init__(self, state_fields, run_kubectl):
        self.state_fields = state_fields
        self.run_kubectl = run_kubectl

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state_fields(index)
        return self.run_kubectl(["get", kind, name, "-n", namespace, "-o", "yaml"])
