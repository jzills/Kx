import json
from dataclasses import asdict
from unittest.mock import MagicMock

from kx.commands.back import BackCommand
from kx.state import State


def _make_command(navigate_result=None):
    state = MagicMock()
    if navigate_result is None:
        navigate_result = State(resources={"nginx": "Pod"}, namespace="default")
    state.navigate.return_value = navigate_result
    return BackCommand(state=state), state


class TestBackCommand:
    def test_calls_navigate_minus_one(self):
        cmd, state = _make_command()
        cmd.execute()
        state.navigate.assert_called_once_with(-1)

    def test_returns_json_string(self):
        result_state = State(resources={"nginx": "Pod"}, namespace="default")
        cmd, _ = _make_command(navigate_result=result_state)
        result = cmd.execute()
        parsed = json.loads(result)
        assert parsed == asdict(result_state)

    def test_returns_navigated_state_as_json(self):
        result_state = State(resources={"myapp": "Deployment"}, namespace="prod")
        cmd, _ = _make_command(navigate_result=result_state)
        result = cmd.execute()
        parsed = json.loads(result)
        assert parsed["namespace"] == "prod"
        assert "myapp" in parsed["resources"]
