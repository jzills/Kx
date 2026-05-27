class EditCommand:
    def __init__(self, state_fields, run_kubectl_interactive):
        self.state_fields = state_fields
        self.run_kubectl_interactive = run_kubectl_interactive

    def execute(self, index: int) -> None:
        name, namespace, kind = self.state_fields(index)
        self.run_kubectl_interactive(["edit", kind, name, "-n", namespace])
