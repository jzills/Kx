from rich.tree import Tree


class TreeCommand:
    def __init__(self, state_fields, build_tree, normalize_kind):
        self.state_fields = state_fields
        self.build_tree = build_tree
        self.normalize_kind = normalize_kind

    def execute(self, index: int) -> Tree:
        name, namespace, kind = self.state_fields(index)
        return self.build_tree(self.normalize_kind(kind), name, namespace)
