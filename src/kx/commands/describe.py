from kx.events import EventsServiceProtocol
from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol


class DescribeCommand:
    def __init__(
        self,
        state: StateServiceProtocol,
        events: EventsServiceProtocol,
        kubectl: KubectlServiceProtocol,
    ):
        self.state = state
        self.events = events
        self.kubectl = kubectl

    def execute(self, index: int, view: str) -> str | None:
        name, namespace, kind = self.state.fields(index)

        if view == "events":
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

        self.kubectl.run_interactive(["describe", kind, name, "-n", namespace])
        return None
