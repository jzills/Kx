import yaml

from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class YamlCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, index: int, show: list[str] | None = None) -> str:
        name, namespace, kind = self.state.fields(index)
        raw = self.kubectl.run(["get", kind, name, "-n", namespace, "-o", "yaml"])
        if not show:
            return raw
        data = yaml.safe_load(raw)
        filtered = {key: data[key] for key in show if key in data}
        return yaml.dump(filtered, default_flow_style=False)
