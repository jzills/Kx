import pytest
from unittest.mock import MagicMock

from kx.commands.rollout import RolloutAction, RolloutCommand
from kx.kinds import Kind


def _make_command(name="my-deploy", namespace="default", kind=Kind.Deployment):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return RolloutCommand(kubectl=kubectl, state=state), state, kubectl


class TestRolloutCommand:
    def test_status_calls_interactive(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1, RolloutAction.status)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "Deployment/my-deploy", "-n", "default"]
        )
        assert result is None

    def test_status_is_default_action(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1)
        kubectl.run_interactive.assert_called_once()
        assert result is None

    def test_restart_calls_run(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = "Deployment/my-deploy restarted"
        result = cmd.execute(1, RolloutAction.restart)
        kubectl.run.assert_called_once_with(
            ["rollout", "restart", "Deployment/my-deploy", "-n", "default"]
        )
        assert result == "Deployment/my-deploy restarted"

    def test_pause_calls_run(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = "Deployment/my-deploy paused"
        result = cmd.execute(1, RolloutAction.pause)
        kubectl.run.assert_called_once_with(
            ["rollout", "pause", "Deployment/my-deploy", "-n", "default"]
        )
        assert result == "Deployment/my-deploy paused"

    def test_resume_calls_run(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = "Deployment/my-deploy resumed"
        result = cmd.execute(1, RolloutAction.resume)
        kubectl.run.assert_called_once_with(
            ["rollout", "resume", "Deployment/my-deploy", "-n", "default"]
        )
        assert result == "Deployment/my-deploy resumed"

    def test_history_calls_run(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = "REVISION  CHANGE-CAUSE\n1         <none>"
        result = cmd.execute(1, RolloutAction.history)
        kubectl.run.assert_called_once_with(
            ["rollout", "history", "Deployment/my-deploy", "-n", "default"]
        )
        assert "REVISION" in result

    def test_undo_calls_run(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = "deployment.apps/my-deploy rolled back"
        result = cmd.execute(1, RolloutAction.undo)
        kubectl.run.assert_called_once_with(
            ["rollout", "undo", "Deployment/my-deploy", "-n", "default"]
        )
        assert result == "deployment.apps/my-deploy rolled back"

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command()
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_statefulset_status(self):
        cmd, _, kubectl = _make_command(name="my-sts", kind=Kind.StatefulSet)
        cmd.execute(1, RolloutAction.status)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "StatefulSet/my-sts", "-n", "default"]
        )

    def test_daemonset_status(self):
        cmd, _, kubectl = _make_command(name="my-ds", kind=Kind.DaemonSet)
        cmd.execute(1, RolloutAction.status)
        kubectl.run_interactive.assert_called_once_with(
            ["rollout", "status", "DaemonSet/my-ds", "-n", "default"]
        )

    def test_statefulset_restart(self):
        cmd, _, kubectl = _make_command(
            name="my-sts", namespace="staging", kind=Kind.StatefulSet
        )
        kubectl.run.return_value = "StatefulSet/my-sts restarted"
        result = cmd.execute(1, RolloutAction.restart)
        kubectl.run.assert_called_once_with(
            ["rollout", "restart", "StatefulSet/my-sts", "-n", "staging"]
        )
        assert result == "StatefulSet/my-sts restarted"

    def test_unsupported_kind_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Pod)
        with pytest.raises(ValueError, match="rollout is not supported for 'Pod'"):
            cmd.execute(1, RolloutAction.status)

    def test_unsupported_kind_restart_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Service)
        with pytest.raises(ValueError, match="rollout is not supported for 'Service'"):
            cmd.execute(1, RolloutAction.restart)

    def test_unsupported_kind_pause_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Pod)
        with pytest.raises(ValueError, match="rollout is not supported for 'Pod'"):
            cmd.execute(1, RolloutAction.pause)

    def test_unsupported_kind_undo_raises(self):
        cmd, _, _ = _make_command(kind=Kind.ReplicaSet)
        with pytest.raises(
            ValueError, match="rollout is not supported for 'ReplicaSet'"
        ):
            cmd.execute(1, RolloutAction.undo)
