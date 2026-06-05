from unittest.mock import MagicMock
from kx.commands.get import GetCommand
from kx.kinds import Kind


def _make_command(kubectl_output="NAME\nnginx"):
    kubectl = MagicMock()
    kubectl.run.return_value = kubectl_output
    kubectl.current_namespace.return_value = "default"
    state = MagicMock()
    index = MagicMock()
    index.add.return_value = ("1  nginx", ["nginx"])
    return GetCommand(kubectl=kubectl, state=state, index=index), state, kubectl


class TestGetCommandExtraArgs:
    def test_extra_args_passed_through(self):
        cmd, _, kubectl = _make_command()
        cmd.execute("pods", "default", extra_args=["-o", "wide"])
        kubectl.run.assert_called_once_with(["get", "pods", "-n", "default", "-o", "wide"])

    def test_multiple_extra_args(self):
        cmd, _, kubectl = _make_command()
        cmd.execute("pods", "default", extra_args=["--field-selector", "status.phase=Running"])
        kubectl.run.assert_called_once_with(
            ["get", "pods", "-n", "default", "--field-selector", "status.phase=Running"]
        )


class TestGetCommandNonTabularOutput:
    def test_json_output_does_not_save_state(self):
        cmd, state, kubectl = _make_command()
        cmd.index.add.return_value = ('{\n  "items": []\n}', [])
        kubectl.run.return_value = '{\n  "items": []\n}'
        cmd.execute("pods", "default", extra_args=["-o", "json"])
        state.save.assert_not_called()


class TestGetCommandNormalizesKind:
    def test_alias_normalized_to_canonical_kind(self):
        cmd, state, _ = _make_command()
        cmd.execute("po", "default")
        saved = state.save.call_args[0][0]
        assert saved.kind == str(Kind.Pod)

    def test_plural_alias_normalized(self):
        cmd, state, _ = _make_command()
        cmd.execute("pods", "default")
        saved = state.save.call_args[0][0]
        assert saved.kind == str(Kind.Pod)

    def test_deploy_alias_normalized(self):
        cmd, state, _ = _make_command()
        cmd.execute("deploy", "default")
        saved = state.save.call_args[0][0]
        assert saved.kind == str(Kind.Deployment)

    def test_unknown_crd_passes_through(self):
        cmd, state, _ = _make_command()
        cmd.execute("mycrd", "default")
        saved = state.save.call_args[0][0]
        assert saved.kind == "mycrd"
