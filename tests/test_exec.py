import pytest
from unittest.mock import MagicMock
from kx.commands.exec import ExecCommand
from kx.kinds import Kind


def _make_command(name="nginx", namespace="default", kind=Kind.Pod):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    kubectl.run_interactive.return_value = 0
    return ExecCommand(state=state, kubectl=kubectl), state, kubectl


class TestExecCommand:
    def test_default_shell_bash(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, None)
        kubectl.run_interactive.assert_called_once_with(
            ["exec", "-it", "nginx", "-n", "default", "--", "bash"]
        )

    def test_falls_back_to_sh_when_bash_fails(self):
        cmd, _, kubectl = _make_command()
        kubectl.run_interactive.return_value = 1
        cmd.execute(1, None)
        assert kubectl.run_interactive.call_count == 2
        kubectl.run_interactive.assert_called_with(
            ["exec", "-it", "nginx", "-n", "default", "--", "sh"]
        )

    def test_explicit_cmd(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["python3"])
        kubectl.run_interactive.assert_called_once_with(
            ["exec", "-it", "nginx", "-n", "default", "--", "python3"]
        )

    def test_non_pod_raises_value_error(self):
        cmd, _, _ = _make_command(kind=Kind.Deployment)
        with pytest.raises(ValueError, match="exec is only supported for pods"):
            cmd.execute(1, None)

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-pod", namespace="kube-system")
        cmd.execute(3, None)
        state.fields.assert_called_once_with(3)

    def test_extra_args_with_default_shell(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, None, extra_args=["-c", "sidecar"])
        kubectl.run_interactive.assert_called_once_with(
            ["exec", "-it", "nginx", "-n", "default", "-c", "sidecar", "--", "bash"]
        )

    def test_extra_args_with_explicit_cmd(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["sh"], extra_args=["-c", "sidecar"])
        kubectl.run_interactive.assert_called_once_with(
            ["exec", "-it", "nginx", "-n", "default", "-c", "sidecar", "--", "sh"]
        )
