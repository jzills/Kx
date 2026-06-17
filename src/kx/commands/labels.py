import json

from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class LabelsCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int) -> dict[str, str]:
        name, namespace, kind = self.state.fields(index)
        raw = self.kubectl.run(["get", kind, name, "-n", namespace, "-o", "json"])
        obj = json.loads(raw)
        return obj.get("metadata", {}).get("labels") or {}
