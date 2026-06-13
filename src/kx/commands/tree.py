from rich.tree import Tree

from kx.kubectl import KubectlServiceProtocol
from kx.state import State, StateServiceProtocol
from kx.types import BuildIndexedTree, BuildTree


class TreeCommand:
    def __init__(
        self,
        state: StateServiceProtocol,
        kubectl: KubectlServiceProtocol,
        build_tree: BuildTree,
        build_indexed_tree: BuildIndexedTree,
    ):
        self.state = state
        self.kubectl = kubectl
        self.build_tree = build_tree
        self.build_indexed_tree = build_indexed_tree

    def execute(self, index: int, indexed: bool = False) -> Tree:
        name, namespace, kind = self.state.fields(index)
        if indexed:
            tree, resources = self.build_indexed_tree(kind, name, namespace)
            if resources:
                self.state.save(
                    State(
                        resources={name: kind for name, kind in resources},
                        namespace=namespace,
                    )
                )
        else:
            tree = self.build_tree(kind, name, namespace)
        return tree
