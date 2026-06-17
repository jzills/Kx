from unittest.mock import MagicMock

from kx.commands.namespace import NamespaceCommand


def _make_command(namespace_name="production"):
    kubectl = MagicMock()
    state = MagicMock()
    state.fields.return_value = (namespace_name, "default", "Namespace")
    return NamespaceCommand(kubectl=kubectl, state=state), state, kubectl


class TestNamespaceCommandExecute:
    def test_resolves_index_from_state(self):
        cmd, state, _ = _make_command()
        cmd.execute(2)
        state.fields.assert_called_once_with(2)

    def test_sets_context_to_resolved_name(self):
        cmd, _, kubectl = _make_command("staging")
        cmd.execute(1)
        kubectl.run.assert_called_once_with(
            ["config", "set-context", "--current", "--namespace=staging"]
        )

    def test_returns_namespace_name(self):
        cmd, _, _ = _make_command("production")
        assert cmd.execute(1) == "production"

    def test_raises_on_invalid_index(self):
        kubectl = MagicMock()
        state = MagicMock()
        state.fields.side_effect = RuntimeError("Index out of range")
        cmd = NamespaceCommand(kubectl=kubectl, state=state)
        try:
            cmd.execute(99)
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass

    def test_raises_on_kubectl_error(self):
        kubectl = MagicMock()
        kubectl.run.side_effect = RuntimeError("kubectl failed")
        state = MagicMock()
        state.fields.return_value = ("production", "default", "Namespace")
        cmd = NamespaceCommand(kubectl=kubectl, state=state)
        try:
            cmd.execute(1)
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass
