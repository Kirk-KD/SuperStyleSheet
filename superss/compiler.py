from typing import Dict

from superss import RootNode, StyleBodyNode, MixinDefNode


class Compiler:
    def __init__(self, root_node: RootNode):
        self._root_node: RootNode = root_node
        self._mixin_table: Dict[str, StyleBodyNode] = {}

    def _traverse(self):
        self._mixin_table = {}

        for statement in self._root_node.statements:
            if isinstance(statement, MixinDefNode):
                if statement.symbol.value in self._mixin_table:
                    raise ValueError(statement.symbol)
                self._mixin_table[statement.symbol.value] = statement.style_body_node

    def compile_css(self, minified: bool = True):
        self._traverse()
        return (self._root_node.parse_min_css if minified else self._root_node.parse_css)(compiler=self)

    def get_mixin(self, name: str) -> StyleBodyNode:
        return self._mixin_table[name]
