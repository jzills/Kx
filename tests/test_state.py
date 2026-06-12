import pytest
from typer import Exit as ClickExit
from unittest.mock import patch
from kx.state import State, StateService


def _patched(tmp_path):
    return patch("kx.state._STATE_FILE", tmp_path / "kx_state.json")


class TestStateDataclass:
    def test_default_namespace_is_default(self):
        state = State(resources={"nginx": "Pod"})
        assert state.namespace == "default"

    def test_fields_are_set(self):
        state = State(resources={"app": "Deployment"}, namespace="staging")
        assert state.resources == {"app": "Deployment"}
        assert state.namespace == "staging"


class TestStateServiceSaveLoad:
    def test_round_trip(self, tmp_path):
        state = State(resources={"nginx": "Pod", "redis": "Pod"}, namespace="kube-system")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            loaded = svc.load()
        assert loaded == state

    def test_round_trip_default_namespace(self, tmp_path):
        state = State(resources={"app": "Pod"})
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
        state = State(resources={"nginx": "Pod"})
        with patch("kx.state._STATE_FILE", state_file):
            StateService().save(state)
        assert state_file.exists()


class TestStateServiceFields:
    def test_fields_index_1(self, tmp_path):
        state = State(resources={"nginx": "Pod", "redis": "Pod"}, namespace="kube-system")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            name, namespace, kind = svc.fields(1)
        assert name == "nginx"
        assert namespace == "kube-system"
        assert kind == "Pod"

    def test_fields_index_2(self, tmp_path):
        state = State(resources={"nginx": "Pod", "redis": "Pod"}, namespace="default")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            name, _, _ = svc.fields(2)
        assert name == "redis"

    def test_fields_heterogeneous_kinds(self, tmp_path):
        state = State(resources={"my-rs": "ReplicaSet", "my-pod": "Pod"}, namespace="default")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            _, _, kind1 = svc.fields(1)
            _, _, kind2 = svc.fields(2)
        assert kind1 == "ReplicaSet"
        assert kind2 == "Pod"

    def test_fields_invalid_index_raises(self, tmp_path):
        state = State(resources={"nginx": "Pod"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            with pytest.raises(ClickExit):
                svc.fields(0)

    def test_fields_out_of_bounds_raises(self, tmp_path):
        state = State(resources={"nginx": "Pod"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            with pytest.raises(ClickExit):
                svc.fields(5)
