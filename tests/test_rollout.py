import pytest
from unittest.mock import MagicMock

from kx.commands.rollout import RolloutCommand
from kx.kinds import Kind


def _make_command(name="my-deploy", namespace="default", kind=Kind.Deployment):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return RolloutCommand(kubectl=kubectl, state=state), state, kubectl


class TestRolloutCommand:
    def test_status_calls_interactive(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "Deployment/my-deploy", "-n", "default"]
        )
        assert result is None

    def test_restart_calls_run(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1, restart=True)
        kubectl.run.assert_called_once_with(
            ["rollout", "restart", "Deployment/my-deploy", "-n", "default"]
        )
        assert result == "Restarted Deployment/my-deploy"

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command()
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_statefulset_status(self):
        cmd, _, kubectl = _make_command(name="my-sts", kind=Kind.StatefulSet)
        cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "StatefulSet/my-sts", "-n", "default"]
        )

    def test_daemonset_status(self):
        cmd, _, kubectl = _make_command(name="my-ds", kind=Kind.DaemonSet)
        cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "DaemonSet/my-ds", "-n", "default"]
        )

    def test_statefulset_restart(self):
        cmd, _, kubectl = _make_command(
            name="my-sts", namespace="staging", kind=Kind.StatefulSet
        )
        result = cmd.execute(1, restart=True)
        kubectl.run.assert_called_once_with(
            ["rollout", "restart", "StatefulSet/my-sts", "-n", "staging"]
        )
        assert result == "Restarted StatefulSet/my-sts"

    def test_unsupported_kind_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Pod)
        with pytest.raises(ValueError, match="rollout is not supported for 'Pod'"):
            cmd.execute(1)

    def test_unsupported_kind_restart_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Service)
        with pytest.raises(ValueError, match="rollout is not supported for 'Service'"):
            cmd.execute(1, restart=True)
