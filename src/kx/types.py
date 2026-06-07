from collections.abc import Callable

from rich.tree import Tree

Confirm   = Callable[[str], None]
BuildTree = Callable[[str, str, str], Tree]
