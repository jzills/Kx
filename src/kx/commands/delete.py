class DeleteCommand:
    def __init__(self, state_fields, run_kubectl, confirm):
        self.state_fields = state_fields
        self.run_kubectl = run_kubectl
        self.confirm = confirm

    def execute(self, index: int, yes: bool) -> str:
        name, namespace, kind = self.state_fields(index)
        if not yes:
            self.confirm(f"Delete {kind}/{name} in {namespace}?")
        self.run_kubectl(["delete", kind, name, "-n", namespace])
        return f"Deleted {kind}/{name}"
