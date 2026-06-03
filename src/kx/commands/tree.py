from rich.tree import Tree

from kx.kubectl import KubectlServiceProtocol
from kx.state import StateServiceProtocol
from kx.types import BuildTree


class TreeCommand:
    def __init__(self, state: StateServiceProtocol, kubectl: KubectlServiceProtocol, build_tree: BuildTree):
        self.state = state
        self.kubectl = kubectl
        self.build_tree = build_tree

    def execute(self, index: int) -> Tree:
        name, namespace, kind = self.state.fields(index)
        return self.build_tree(self.kubectl.normalize_kind(kind), name, namespace)
