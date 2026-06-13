from collections.abc import Callable

from rich.tree import Tree

Confirm = Callable[[str], None]
BuildTree = Callable[[str, str, str], Tree]
BuildIndexedTree = Callable[[str, str, str], tuple[Tree, list[tuple[str, str]]]]
