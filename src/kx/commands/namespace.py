import json
import re
from dataclasses import asdict

from kx.kinds import normalize_kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import State, StateServiceProtocol


def _parse_all_output(output: str) -> dict:
    resources = {}
    for section in re.split(r"\n\s*\n", output.strip()):
        lines = [line for line in section.splitlines() if line.strip()]
        if not lines or "NAME" not in lines[0].split():
            continue
        spans = [(m.start(), m.end()) for m in re.finditer(r"\S+\s*", lines[0])]
        name_idx = next(
            (
                index
                for index, (start, end) in enumerate(spans)
                if lines[0][start:end].strip() == "NAME"
            ),
            None,
        )
        if name_idx is None:
            continue
        for line in lines[1:]:
            cols = [line[start:end].strip() for start, end in spans]
            if name_idx >= len(cols):
                continue
            raw_name = cols[name_idx]
            if "/" not in raw_name:
                continue
            prefix, bare_name = raw_name.split("/", 1)
            resources[bare_name] = normalize_kind(prefix.split(".")[0])
    return resources


class NamespaceCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol):
        self.state = state
        self.kubectl = kubectl

    def execute(self, namespace: str) -> str:
        self.kubectl.run(
            ["config", "set-context", "--current", f"--namespace={namespace}"]
        )
        output = self.kubectl.run(["get", "all", "-n", namespace])
        resources = _parse_all_output(output)
        state = State(resources=resources, namespace=namespace)
        self.state.save(state)
        return json.dumps(asdict(state), indent=2)
