from unittest.mock import MagicMock

from kx.commands.drop import DropCommand
from kx.state import State, StateHistory


def _make_command(history=None):
    state = MagicMock()
    if history is None:
        history = StateHistory(
            states=[
                State(resources={"nginx": "Pod"}),
                State(resources={"myapp": "Deployment"}),
            ],
            cursor=1,
        )
    state.drop.return_value = history
    return DropCommand(state=state), state


class TestDropCommand:
    def test_calls_drop_with_position(self):
        cmd, state = _make_command()
        cmd.execute(2)
        state.drop.assert_called_once_with(2)

    def test_returns_state_history(self):
        history = StateHistory(states=[State(resources={"nginx": "Pod"})], cursor=0)
        cmd, _ = _make_command(history=history)
        result = cmd.execute(1)
        assert result is history
