from unittest.mock import MagicMock
from kx.commands.edit import EditCommand
from kx.kinds import Kind


def _make_command(name="nginx", namespace="default", kind=str(Kind.Pod)):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return EditCommand(state=state, kubectl=kubectl), state, kubectl


class TestEditCommand:
    def test_basic_edit(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1)
        kubectl.run_interactive.assert_called_once_with(
            ["edit", "Pod", "nginx", "-n", "default"]
        )

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-pod", namespace="kube-system")
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_extra_args_passed_through(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["--record"])
        kubectl.run_interactive.assert_called_once_with(
            ["edit", "Pod", "nginx", "-n", "default", "--record"]
        )

    def test_multiple_extra_args(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1, ["--record", "--save-config"])
        kubectl.run_interactive.assert_called_once_with(
            ["edit", "Pod", "nginx", "-n", "default", "--record", "--save-config"]
        )
