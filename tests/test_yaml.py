import yaml
from unittest.mock import MagicMock

from kx.commands.yaml import YamlCommand
from kx.kinds import Kind

_SAMPLE_YAML = yaml.dump(
    {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {"name": "nginx", "namespace": "default"},
        "spec": {"containers": [{"name": "nginx", "image": "nginx:latest"}]},
        "status": {"phase": "Running"},
    }
)


def _make_command(
    name="nginx", namespace="default", kind=str(Kind.Pod), raw_yaml=_SAMPLE_YAML
):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    kubectl.run.return_value = raw_yaml
    return YamlCommand(state=state, kubectl=kubectl), state, kubectl


class TestYamlCommand:
    def test_no_show_returns_raw_yaml(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1)
        assert result == _SAMPLE_YAML

    def test_show_single_key(self):
        cmd, _, _ = _make_command()
        result = cmd.execute(1, show=["spec"])
        parsed = yaml.safe_load(result)
        assert set(parsed.keys()) == {"spec"}
        assert parsed["spec"]["containers"][0]["name"] == "nginx"

    def test_show_multiple_keys(self):
        cmd, _, _ = _make_command()
        result = cmd.execute(1, show=["metadata", "spec"])
        parsed = yaml.safe_load(result)
        assert set(parsed.keys()) == {"metadata", "spec"}

    def test_show_missing_key_silently_omitted(self):
        cmd, _, _ = _make_command()
        result = cmd.execute(1, show=["spec", "nonexistent"])
        parsed = yaml.safe_load(result)
        assert set(parsed.keys()) == {"spec"}

    def test_show_all_missing_keys_returns_empty(self):
        cmd, _, _ = _make_command()
        result = cmd.execute(1, show=["nonexistent"])
        parsed = yaml.safe_load(result)
        assert parsed is None or parsed == {}

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-pod", namespace="kube-system")
        cmd.execute(3)
        state.fields.assert_called_once_with(3)

    def test_kubectl_called_with_correct_args(self):
        cmd, _, kubectl = _make_command()
        cmd.execute(1)
        kubectl.run.assert_called_once_with(
            ["get", str(Kind.Pod), "nginx", "-n", "default", "-o", "yaml"]
        )
