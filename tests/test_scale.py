import pytest
from unittest.mock import MagicMock

from kx.commands.scale import ScaleCommand
from kx.kinds import Kind


def _make_command(name="my-deploy", namespace="default", kind=Kind.Deployment):
    state = MagicMock()
    state.fields.return_value = (name, namespace, kind)
    kubectl = MagicMock()
    return ScaleCommand(kubectl=kubectl, state=state), state, kubectl


class TestScaleCommand:
    def test_basic_scale(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1, 3)
        kubectl.run.assert_called_once_with(
            ["scale", "Deployment/my-deploy", "--replicas=3", "-n", "default"]
        )
        assert result == "Scaled Deployment/my-deploy to 3 replicas"

    def test_singular_replica(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1, 1)
        kubectl.run.assert_called_once_with(
            ["scale", "Deployment/my-deploy", "--replicas=1", "-n", "default"]
        )
        assert result == "Scaled Deployment/my-deploy to 1 replica"

    def test_zero_replicas(self):
        cmd, _, kubectl = _make_command()
        result = cmd.execute(1, 0)
        kubectl.run.assert_called_once_with(
            ["scale", "Deployment/my-deploy", "--replicas=0", "-n", "default"]
        )
        assert result == "Scaled Deployment/my-deploy to 0 replicas"

    def test_uses_state_fields(self):
        cmd, state, _ = _make_command(name="my-sts", kind=Kind.StatefulSet)
        cmd.execute(2, 5)
        state.fields.assert_called_once_with(2)

    def test_statefulset_supported(self):
        cmd, _, kubectl = _make_command(
            name="my-sts", namespace="prod", kind=Kind.StatefulSet
        )
        result = cmd.execute(1, 2)
        kubectl.run.assert_called_once_with(
            ["scale", "StatefulSet/my-sts", "--replicas=2", "-n", "prod"]
        )
        assert result == "Scaled StatefulSet/my-sts to 2 replicas"

    def test_replicaset_supported(self):
        cmd, _, kubectl = _make_command(name="my-rs", kind=Kind.ReplicaSet)
        result = cmd.execute(1, 4)
        kubectl.run.assert_called_once_with(
            ["scale", "ReplicaSet/my-rs", "--replicas=4", "-n", "default"]
        )
        assert result == "Scaled ReplicaSet/my-rs to 4 replicas"

    def test_unsupported_pod_raises(self):
        cmd, _, _ = _make_command(kind=Kind.Pod)
        with pytest.raises(ValueError, match="scale is not supported for 'Pod'"):
            cmd.execute(1, 3)

    def test_unsupported_configmap_raises(self):
        cmd, _, _ = _make_command(kind=Kind.ConfigMap)
        with pytest.raises(ValueError, match="scale is not supported for 'ConfigMap'"):
            cmd.execute(1, 2)
