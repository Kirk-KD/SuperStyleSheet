from typing import TYPE_CHECKING, List, Tuple
from superss import TokenType, Token
if TYPE_CHECKING:
    from superss import Compiler


class Node:
    pass


class CSSNode(Node):
    def parse_css(self, compiler: 'Compiler' = None) -> str:
        raise NotImplemented

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        raise NotImplemented


class RootNode(CSSNode):
    def __init__(self, statements: List[Node]):
        self.statements: List[Node] = statements

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return '\n'.join([stmt.parse_css(compiler) for stmt in self.statements if isinstance(stmt, CSSNode)])

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return ''.join([stmt.parse_min_css(compiler) for stmt in self.statements if isinstance(stmt, CSSNode)])


class StyleNode(CSSNode):
    def __init__(self, selector_node: 'SelectorNode', style_body_node: 'StyleBodyNode',
                 mixin_list: 'IdentifierListNode | None' = None):
        self.selector_node: 'SelectorNode' = selector_node
        self.mixin_list: 'IdentifierListNode | None' = mixin_list
        self.style_body_node: 'StyleBodyNode' = style_body_node

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        selector = self.selector_node.parse_css()
        properties = self.style_body_node.parse_css()
        all_properties = ';\n'.join(
            [compiler.get_mixin(identifier.value).parse_css()
             for identifier in self.mixin_list.identifiers] + [properties]) \
            if self.mixin_list is not None else properties

        self_css = selector + (' {\n' + all_properties + '\n}' if all_properties else ' {}')

        for child in self.style_body_node.children_style_nodes:
            self_css += '\n' + child.parse_css(compiler)

        return self_css

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        selector = self.selector_node.parse_min_css()
        properties = self.style_body_node.parse_min_css()
        all_properties = ';'.join(
            [compiler.get_mixin(identifier.value).parse_min_css()
             for identifier in self.mixin_list.identifiers] + [properties]) \
            if self.mixin_list is not None else properties

        self_css = selector + '{' + all_properties + '}'

        for child in self.style_body_node.children_style_nodes:
            self_css += child.parse_min_css(compiler)

        return self_css


class PropertyNode(CSSNode):
    def __init__(self, property_token: Token, property_value_token: Token):
        self.property_token: Token = property_token
        self.property_value_token: Token = property_value_token

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return f'  {self.property_token.value}: {self.property_value_token.value}'

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return f'{self.property_token.value}:{self.property_value_token.value}'


class SelectorNode(CSSNode):
    def __init__(self, single_selector_nodes: 'List[SingleSelectorNode]', parent_selector_node: 'SelectorNode | None'):
        self.single_selector_nodes: 'List[SingleSelectorNode]' = single_selector_nodes
        self.parent_selector_node: 'SelectorNode | None' = parent_selector_node

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return ', '.join(self.parse_list_css(compiler))

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return ','.join(self.parse_list_min_css(compiler))

    def parse_list_css(self, compiler: 'Compiler' = None) -> List[str]:
        if self.parent_selector_node is None:
            return [single_selector.parse_css(compiler) for single_selector in self.single_selector_nodes]

        combinations = []
        for parent_selector_string in self.parent_selector_node.parse_list_css():
            for single_selector in self.single_selector_nodes:
                single_css = single_selector.parse_css(compiler)
                space = ' ' if single_css[0] not in '+~>' else ''
                combinations.append(parent_selector_string + space + single_css)
        return combinations

    def parse_list_min_css(self, compiler: 'Compiler' = None) -> List[str]:
        if self.parent_selector_node is None:
            return [single_selector.parse_min_css(compiler) for single_selector in self.single_selector_nodes]

        combinations = []
        for parent_selector_string in self.parent_selector_node.parse_list_min_css():
            for single_selector in self.single_selector_nodes:
                single_css = single_selector.parse_min_css(compiler)
                space = ' ' if single_css[0] not in '+~>' else ''
                combinations.append(parent_selector_string + space + single_css)
        return combinations


class SingleSelectorNode(CSSNode):
    def __init__(self,
                 first_selector_sequence_node: 'SelectorSequenceNode',
                 combinator_selector_list: 'List[Tuple[Token, SelectorSequenceNode]]',
                 parent_combinator: 'Token | None'):
        self.first_selector_sequence_node: 'SelectorSequenceNode' = first_selector_sequence_node
        self.combinator_selector_list: 'List[Tuple[Token, SelectorSequenceNode]]' = combinator_selector_list
        self.parent_combinator: 'Token | None' = parent_combinator

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        combinator = self.parent_combinator.value if self.parent_combinator is not None else ''
        css = combinator + self.first_selector_sequence_node.parse_css()
        for combinator, selector in self.combinator_selector_list:
            comb = (' ' + combinator.value + ' ') if combinator.type != TokenType.SPACE else ' '
            css += f'{comb}{selector.parse_css()}'
        return css

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        combinator = self.parent_combinator.value if self.parent_combinator is not None else ''
        css = combinator + self.first_selector_sequence_node.parse_min_css()
        for combinator, selector in self.combinator_selector_list:
            comb = combinator.value
            css += f'{comb}{selector.parse_min_css()}'
        return css


class AttributeSelectorNode(CSSNode):
    def __init__(self, attribute: Token, operator: Token | None = None, value: Token | None = None):
        self.attribute = attribute
        self.operator = operator
        self.value = value

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        if self.operator is None:
            return f'[{self.attribute.value}]'
        value = f'"{self.value.value}"' if self.value.type == TokenType.STRING else self.value.value
        return f'[{self.attribute.value} {self.operator.value} {value}]'

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        if self.operator is None:
            return f'[{self.attribute.value}]'
        value = f'"{self.value.value}"' if self.value.type == TokenType.STRING else self.value.value
        return f'[{self.attribute.value}{self.operator.value}{value}]'


class SelectorSequenceNode(CSSNode):
    def __init__(self, sequence: List[Token], pseudo_class_node: 'Token | None' = None,
                 pseudo_element_node: 'Token | None' = None,
                 attribute_selectors: 'List[AttributeSelectorNode] | None' = None):
        self.sequence: List[Token] = sequence
        self.pseudo_class_node: 'PseudoClassNode | None' = pseudo_class_node
        self.pseudo_element_node: 'PseudoElementNode | None' = pseudo_element_node
        self.attribute_selectors: 'List[AttributeSelectorNode] | None' = attribute_selectors

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        css = ''.join([token.value for token in self.sequence])
        for attr in self.attribute_selectors:
            css += attr.parse_css(compiler)
        if self.pseudo_class_node is not None:
            css += self.pseudo_class_node.parse_css(compiler)
        if self.pseudo_element_node is not None:
            css += self.pseudo_element_node.parse_css(compiler)
        return css

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        css = ''.join([token.value for token in self.sequence])
        for attr in self.attribute_selectors:
            css += attr.parse_min_css(compiler)
        if self.pseudo_class_node is not None:
            css += self.pseudo_class_node.parse_min_css(compiler)
        if self.pseudo_element_node is not None:
            css += self.pseudo_element_node.parse_min_css(compiler)
        return css


class PseudoClassNode(CSSNode):
    def __init__(self, identifier: Token, attr_selector_nodes: List[AttributeSelectorNode]):
        self.identifier = identifier
        self.attr_selector_nodes = attr_selector_nodes

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return f':{self.identifier.value}{"".join(attr.parse_css() for attr in self.attr_selector_nodes)}'

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return f':{self.identifier.value}{"".join(attr.parse_min_css() for attr in self.attr_selector_nodes)}'


class PseudoElementNode(CSSNode):
    def __init__(self, identifier: Token, attr_selector_nodes: List[AttributeSelectorNode]):
        self.identifier = identifier
        self.attr_selector_nodes = attr_selector_nodes

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return f'::{self.identifier.value}{"".join(attr.parse_css() for attr in self.attr_selector_nodes)}'

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return f'::{self.identifier.value}{"".join(attr.parse_min_css() for attr in self.attr_selector_nodes)}'


class StyleBodyNode(CSSNode):
    def __init__(self, property_nodes: 'List[PropertyNode]', children_style_nodes: 'List[StyleNode]'):
        self.property_nodes = property_nodes
        self.children_style_nodes = children_style_nodes

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return ';\n'.join([prop.parse_css() for prop in self.property_nodes])

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return ';'.join([prop.parse_min_css() for prop in self.property_nodes])


class MixinDefNode(Node):
    def __init__(self, symbol: Token, style_body_node: StyleBodyNode):
        self.symbol = symbol
        self.style_body_node = style_body_node


class IdentifierListNode(Node):
    def __init__(self, identifiers: List[Token]):
        self.identifiers = identifiers
