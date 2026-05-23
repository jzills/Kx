import subprocess


def run_kubectl(args: list[str]) -> str:
    result = subprocess.run(
        ["kubectl", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def run_kubectl_interactive(args: list[str]) -> int:
    result = subprocess.run(["kubectl", *args])
    return result.returncode