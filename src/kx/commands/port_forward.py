_SUPPORTED_KINDS = {"Pod", "Deployment", "ReplicaSet", "StatefulSet", "DaemonSet", "Service"}


class PortForwardCommand:
    def __init__(self, run_kubectl_interactive, state_fields, normalize_kind):
        self.run_kubectl_interactive = run_kubectl_interactive
        self.state_fields = state_fields
        self.normalize_kind = normalize_kind

    def execute(self, index: int, port: str) -> None:
        name, namespace, kind = self.state_fields(index)
        canonical = self.normalize_kind(kind)
        if canonical not in _SUPPORTED_KINDS:
            raise ValueError(f"port-forward is not supported for '{kind}'.")
        self.run_kubectl_interactive(["port-forward", f"{canonical}/{name}", port, "-n", namespace])