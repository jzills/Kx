import json
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
        state = State(
            resources={"nginx": "Pod", "redis": "Pod"}, namespace="kube-system"
        )
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

    def test_load_returns_most_recent_after_multiple_saves(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"}, namespace="default")
        state2 = State(resources={"myapp": "Deployment"}, namespace="prod")
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            loaded = svc.load()
        assert loaded == state2

    def test_legacy_format_loads_correctly(self, tmp_path):
        state_file = tmp_path / "kx_state.json"
        state_file.write_text(
            json.dumps({"resources": {"nginx": "Pod"}, "namespace": "staging"})
        )
        with patch("kx.state._STATE_FILE", state_file):
            loaded = StateService().load()
        assert loaded == State(resources={"nginx": "Pod"}, namespace="staging")


class TestStateServiceHistory:
    def test_history_preserves_previous_states(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"})
        state2 = State(resources={"myapp": "Deployment"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            history = svc._load_history()
        assert len(history.states) == 2
        assert history.states[0] == state1
        assert history.states[1] == state2
        assert history.cursor == 1

    def test_history_capped_at_max(self, tmp_path):
        with _patched(tmp_path):
            svc = StateService()
            for number in range(12):
                svc.save(State(resources={f"pod-{number}": "Pod"}))
            history = svc._load_history()
        assert len(history.states) == 10

    def test_history_cap_drops_oldest(self, tmp_path):
        with _patched(tmp_path):
            svc = StateService()
            for number in range(11):
                svc.save(State(resources={f"pod-{number}": "Pod"}))
            history = svc._load_history()
        assert "pod-0" not in history.states[0].resources
        assert "pod-1" in history.states[0].resources

    def test_navigate_back_returns_previous_state(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"})
        state2 = State(resources={"myapp": "Deployment"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            result = svc.navigate(-1)
        assert result == state1

    def test_navigate_forward_returns_newer_state(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"})
        state2 = State(resources={"myapp": "Deployment"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            svc.navigate(-1)
            result = svc.navigate(+1)
        assert result == state2

    def test_navigate_back_clamps_at_oldest(self, tmp_path):
        state = State(resources={"nginx": "Pod"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            result = svc.navigate(-1)
        assert result == state

    def test_navigate_forward_clamps_at_newest(self, tmp_path):
        state = State(resources={"nginx": "Pod"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state)
            result = svc.navigate(+1)
        assert result == state

    def test_new_save_after_back_truncates_forward_history(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"})
        state2 = State(resources={"myapp": "Deployment"})
        state3 = State(resources={"svc": "Service"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            svc.navigate(-1)  # go back to state1
            svc.save(state3)  # should replace state2 in forward history
            history = svc._load_history()
        assert len(history.states) == 2
        assert history.states[0] == state1
        assert history.states[1] == state3

    def test_navigate_persists_cursor(self, tmp_path):
        state1 = State(resources={"nginx": "Pod"})
        state2 = State(resources={"myapp": "Deployment"})
        with _patched(tmp_path):
            svc = StateService()
            svc.save(state1)
            svc.save(state2)
            svc.navigate(-1)
            loaded = svc.load()
        assert loaded == state1


class TestStateServiceFields:
    def test_fields_index_1(self, tmp_path):
        state = State(
            resources={"nginx": "Pod", "redis": "Pod"}, namespace="kube-system"
        )
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
        state = State(
            resources={"my-rs": "ReplicaSet", "my-pod": "Pod"}, namespace="default"
        )
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
