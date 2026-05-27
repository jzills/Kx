class EventsCommand:
    def __init__(self, state_fields, get_events, filter_events):
        self.state_fields = state_fields
        self.get_events = get_events
        self.filter_events = filter_events

    def execute(self, index: int) -> str:
        name, namespace, kind = self.state_fields(index)
        all_events = self.get_events(namespace)
        filtered = self.filter_events(all_events, name, kind)

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
