import json
from unittest.mock import MagicMock

from kx.commands.labels import LabelsCommand
from kx.kinds import Kind


def _make_command(name="nginx", namespace="default", kind=str(Kind.Pod)):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return LabelsCommand(state=state, kubectl=kubectl), state, kubectl


def _kubectl_response(labels: dict) -> str:
    return json.dumps({"metadata": {"labels": labels}})


class TestLabelsCommand:
    def test_returns_labels_dict(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = _kubectl_response({"app": "nginx", "env": "prod"})
        result = cmd.execute(1)
        assert result == {"app": "nginx", "env": "prod"}

    def test_kubectl_args(self):
        cmd, _, kubectl = _make_command(
            name="my-pod", namespace="staging", kind=str(Kind.Pod)
        )
        kubectl.run.return_value = _kubectl_response({})
        cmd.execute(2)
        kubectl.run.assert_called_once_with(
            ["get", str(Kind.Pod), "my-pod", "-n", "staging", "-o", "json"]
        )

    def test_uses_state_fields(self):
        cmd, state, kubectl = _make_command()
        kubectl.run.return_value = _kubectl_response({})
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_empty_labels_returns_empty_dict(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = json.dumps({"metadata": {}})
        result = cmd.execute(1)
        assert result == {}

    def test_null_labels_returns_empty_dict(self):
        cmd, _, kubectl = _make_command()
        kubectl.run.return_value = json.dumps({"metadata": {"labels": None}})
        result = cmd.execute(1)
        assert result == {}

    def test_multiple_labels(self):
        cmd, _, kubectl = _make_command(kind=str(Kind.Deployment))
        expected = {"app": "api", "env": "prod", "version": "v1", "managed-by": "helm"}
        kubectl.run.return_value = _kubectl_response(expected)
        result = cmd.execute(1)
        assert result == expected
