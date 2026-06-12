from unittest.mock import MagicMock
from kx.commands.describe import DescribeCommand
from kx.kinds import Kind


def _make_command(name="nginx", namespace="default", kind=str(Kind.Pod)):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return DescribeCommand(state=state, kubectl=kubectl), state, kubectl


class TestDescribeCommand:
    def test_basic_describe(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(
            ["describe", "Pod", "nginx", "-n", "default"]
        )

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-pod", namespace="kube-system")
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_extra_args_passed_through(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["--show-events=false"])
        kubectl.run_interactive.assert_called_once_with(
            ["describe", "Pod", "nginx", "-n", "default", "--show-events=false"]
        )

    def test_multiple_extra_args(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["--show-events=false", "--chunk-size=500"])
        kubectl.run_interactive.assert_called_once_with(
            [
                "describe",
                "Pod",
                "nginx",
                "-n",
                "default",
                "--show-events=false",
                "--chunk-size=500",
            ]
        )
