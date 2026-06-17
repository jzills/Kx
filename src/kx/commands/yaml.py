import yaml

from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


def _find_keys(data: dict | list, keys: set[str]) -> dict:
    result = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if k in keys:
                result[k] = v
            else:
                result.update(_find_keys(v, keys))
    elif isinstance(data, list):
        for item in data:
            result.update(_find_keys(item, keys))
    return result


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
        return yaml.dump(_find_keys(data, set(show)), default_flow_style=False)
