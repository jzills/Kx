import pytest
from click.exceptions import Exit as ClickExit
from unittest.mock import patch
from kx.state import State, StateService


def _patched(tmp_path):
    """Returns a context manager that redirects _STATE_FILE to a temp path."""
    return patch("kx.state._STATE_FILE", tmp_path / "kx_state.json")


class TestStateDataclass:
    def test_default_namespace_is_default(self):
        state = State(resource_type="pods", names=["nginx"])
        assert state.namespace == "default"

    def test_fields_are_set(self):
        state = State(resource_type="deployments", names=["app"], namespace="staging")
        assert state.resource_type == "deployments"
        assert state.names == ["app"]
        assert state.namespace == "staging"


class TestStateServiceSaveLoad:
    def test_round_trip(self, tmp_path):
        state = State(resource_type="pods", names=["nginx", "redis"], namespace="kube-system")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            loaded = svc.load()
        assert loaded == state

    def test_round_trip_default_namespace(self, tmp_path):
        state = State(resource_type="pods", names=["app"])
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            loaded = svc.load()
        assert loaded.namespace == "default"

    def test_load_missing_file_raises_runtime_error(self, tmp_path):
        with _patched(tmp_path):
            svc = StateService()
            with pytest.raises(RuntimeError, match="kx get"):
                svc.load()

    def test_save_writes_json_file(self, tmp_path):
        state_file = tmp_path / "kx_state.json"
        state = State(resource_type="pods", names=["nginx"])
        with patch("kx.state._STATE_FILE", state_file):
            StateService().save(state)
        assert state_file.exists()


class TestStateServiceFields:
    def test_fields_index_1(self, tmp_path):
        state = State(resource_type="pods", names=["nginx", "redis"], namespace="kube-system")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            name, namespace, resource_type = svc.fields(1)
        assert name == "nginx"
        assert namespace == "kube-system"
        assert resource_type == "pods"

    def test_fields_index_2(self, tmp_path):
        state = State(resource_type="pods", names=["nginx", "redis"], namespace="default")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            name, _, _ = svc.fields(2)
        assert name == "redis"

    def test_fields_invalid_index_raises(self, tmp_path):
        state = State(resource_type="pods", names=["nginx"])
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            with pytest.raises(ClickExit):
                svc.fields(0)

    def test_fields_out_of_bounds_raises(self, tmp_path):
        state = State(resource_type="pods", names=["nginx"])
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            with pytest.raises(ClickExit):
                svc.fields(5)
