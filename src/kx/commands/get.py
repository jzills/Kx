from kx.state import KxState


class GetCommand:
    def __init__(self, run_kubectl, add_indexes, save_state, get_namespace):
        self.run_kubectl = run_kubectl
        self.add_indexes = add_indexes
        self.save_state = save_state
        self.get_namespace = get_namespace

    def execute(self, resource: str, namespace: str) -> str:
        """List resources and assign index numbers for use with other commands."""
        if namespace is None:
            namespace = self.get_namespace()

        output = self.run_kubectl(["get", resource, "-n", namespace])
        indexed_output, names = self.add_indexes(output)
        self.save_state(KxState(resource_type=resource, names=names, namespace=namespace))
        return indexed_output
