import pytest
from unittest.mock import MagicMock
from kx.commands.logs import LogsCommand
from kx.kinds import Kind


def _make_command(name="nginx", namespace="default", kind="pods"):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    kubectl.normalize_kind.return_value = Kind.Pod
    kubectl.run_interactive.return_value = 0
    return LogsCommand(state=state, kubectl=kubectl), state, kubectl


class TestLogsCommand:
    def test_basic_logs_no_extra_args(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(["logs", "nginx", "-n", "default"])

    def test_follow_flag(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["-f"])
        kubectl.run_interactive.assert_called_once_with(["logs", "nginx", "-n", "default", "-f"])

    def test_multiple_flags(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["-c", "sidecar", "--tail=50"])
        kubectl.run_interactive.assert_called_once_with(
            ["logs", "nginx", "-n", "default", "-c", "sidecar", "--tail=50"]
        )

    def test_returns_none(self):
        cmd, _, _ = _make_command()
        result = cmd.execute(1)
        assert result is None

    def test_non_pod_raises_value_error(self):
        cmd, _, kubectl = _make_command(kind="deployments")
        kubectl.normalize_kind.return_value = Kind.Deployment
        with pytest.raises(ValueError, match="Logs are only supported on pods"):
            cmd.execute(1)

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-pod", namespace="kube-system")
        cmd.execute(3)
        state.fields.assert_called_once_with(3)
