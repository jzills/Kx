class DescribeCommand:
    def __init__(self, state_fields, get_events, filter_events, run_kubectl_interactive):
        self.state_fields = state_fields
        self.get_events = get_events
        self.filter_events = filter_events
        self.run_kubectl_interactive = run_kubectl_interactive

    def execute(self, index: int, view: str) -> str | None:
        name, namespace, kind = self.state_fields(index)

        if view == "events":
            all_events = self.get_events(namespace)
            events = self.filter_events(all_events, name, kind)

            if not events:
                return "No events found"

            output = []
            for e in events:
                obj = e.involved_object
                output.append(
                    f"{e.type:8} {e.reason:30} "
                    f"{obj.kind:10} {e.metadata.creation_timestamp} "
                    f"{e.message}"
                )
            return "\n".join(output)

        self.run_kubectl_interactive(["describe", kind, name, "-n", namespace])
        return None