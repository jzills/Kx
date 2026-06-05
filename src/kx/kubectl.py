import subprocess
from typing import Protocol

class KubectlServiceProtocol(Protocol):
    def run(self, args: list[str]) -> str: ...
    def run_interactive(self, args: list[str]) -> int: ...
    def current_namespace(self) -> str: ...


class KubectlService:
    def run(self, args: list[str]) -> str:
        result = subprocess.run(
            ["kubectl", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def run_interactive(self, args: list[str]) -> int:
        result = subprocess.run(["kubectl", *args])
        return result.returncode

    def current_namespace(self) -> str:
        result = subprocess.run(
            ["kubectl", "config", "view", "--minify", "-o", "jsonpath={..namespace}"],
            capture_output=True,
            text=True,
            check=True,
        )
        ns = result.stdout.strip()
        return ns if ns else "default"

