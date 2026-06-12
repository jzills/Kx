from kx.index import IndexServiceProtocol
from kx.kinds import normalize_kind
from kx.kubectl import KubectlServiceProtocol
from kx.state import State, StateServiceProtocol


class GetCommand:
    def __init__(
        self,
        kubectl: KubectlServiceProtocol,
        state: StateServiceProtocol,
        index: IndexServiceProtocol,
    ):
        self.kubectl = kubectl
        self.state = state
        self.index = index

    def execute(
        self,
        resource: str,
        namespace: str,
        filter_term: str | None = None,
        extra_args: list[str] = [],
    ) -> str:
        if namespace is None:
            namespace = self.kubectl.current_namespace()

        output = self.kubectl.run(["get", resource, "-n", namespace, *extra_args])
        if filter_term:
            output = self.index.filter(output, filter_term)
        indexed_output, names = self.index.add(output)
        if names:
            kind = normalize_kind(resource)
            self.state.save(
                State(resources={name: kind for name in names}, namespace=namespace)
            )
        return indexed_output
