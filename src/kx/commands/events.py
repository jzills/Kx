from kx.events import EventsServiceProtocol
from kx.state import StateServiceProtocol


class EventsCommand:
    def __init__(self, state: StateServiceProtocol, events: EventsServiceProtocol):
        self.state = state
        self.events = events

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state.fields(index)
        all_events = self.events.get(namespace)
        filtered = self.events.filter(all_events, name, kind)

        if not filtered:
            return "No events found"

        output = []
        for e in filtered:
            obj = e.involved_object
            output.append(
                f"{e.type:8} {e.reason:30} "
                f"{obj.kind:10} {e.metadata.creation_timestamp} "
                f"{e.message}"
            )
        return "\n".join(output)
