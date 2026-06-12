from rich.tree import Tree

from kx.kubectl import KubectlServiceProtocol
from kx.state import State, StateServiceProtocol
from kx.types import BuildIndexedTree


class TreeCommand:
    def __init__(
        self,
        state: StateServiceProtocol,
        kubectl: KubectlServiceProtocol,
        build_tree: BuildIndexedTree,
    ):
        self.state = state
        self.kubectl = kubectl
        self.build_tree = build_tree

    def execute(self, index: int, indexed: bool = False) -> Tree:
        name, namespace, kind = self.state.fields(index)
        tree, resources = self.build_tree(kind, name, namespace)
        if indexed and resources:
            self.state.save(
                State(
                    resources={name: kind for name, kind in resources},
                    namespace=namespace,
                )
            )
        return tree
