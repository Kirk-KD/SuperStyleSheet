from typing import List, Tuple, TYPE_CHECKING
from collections.abc import Iterable

from src.superss import Token, TokenType, STYLE_BEGIN, COMBINATORS, ATTRIBUTE_OPERATORS

if TYPE_CHECKING:
    from src.superss import Compiler


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

        self_css = selector + ' {\n' + all_properties + '\n}'

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
                 parent_combinator: 'Token | None',
                 pseudo_class_identifier: 'Token | None',
                 pseudo_element_identifier: 'Token | None',
                 attribute_selectors: 'List[AttributeSelectorNode] | None'):
        self.first_selector_sequence_node: 'SelectorSequenceNode' = first_selector_sequence_node
        self.combinator_selector_list: 'List[Tuple[Token, SelectorSequenceNode]]' = combinator_selector_list
        self.parent_combinator: 'Token | None' = parent_combinator
        self.pseudo_class_identifier: 'Token | None' = pseudo_class_identifier
        self.pseudo_element_identifier: 'Token | None' = pseudo_element_identifier
        self.attribute_selectors: 'List[AttributeSelectorNode] | None' = attribute_selectors

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        combinator = self.parent_combinator.value if self.parent_combinator is not None else ''
        css = combinator + self.first_selector_sequence_node.parse_css()
        for combinator, selector in self.combinator_selector_list:
            comb = (' ' + combinator.value + ' ') if combinator.type != TokenType.SPACE else ' '
            css += f'{comb}{selector.parse_css()}'
        if self.pseudo_class_identifier is not None:
            css += ':' + self.pseudo_class_identifier.value
        if self.pseudo_element_identifier is not None:
            css += '::' + self.pseudo_element_identifier.value
        for attr in self.attribute_selectors:
            css += attr.parse_css(compiler)
        return css

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        combinator = self.parent_combinator.value if self.parent_combinator is not None else ''
        css = combinator + self.first_selector_sequence_node.parse_min_css()
        for combinator, selector in self.combinator_selector_list:
            comb = combinator.value
            css += f'{comb}{selector.parse_min_css()}'
        if self.pseudo_class_identifier is not None:
            css += ':' + self.pseudo_class_identifier.value
        if self.pseudo_element_identifier is not None:
            css += '::' + self.pseudo_element_identifier.value
        for attr in self.attribute_selectors:
            css += attr.parse_min_css(compiler)
        return css


class AttributeSelectorNode(CSSNode):
    def __init__(self, attribute: Token, operator: Token, value: Token):
        self.attribute = attribute
        self.operator = operator
        self.value = value

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        value = f'"{self.value.value}"' if self.value.type == TokenType.STRING else self.value.value
        return f'[{self.attribute.value} {self.operator.value} {value}]'

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        value = f'"{self.value.value}"' if self.value.type == TokenType.STRING else self.value.value
        return f'[{self.attribute.value}{self.operator.value}{value}]'


class SelectorSequenceNode(CSSNode):
    def __init__(self, sequence: List[Token]):
        self.sequence: List[Token] = sequence

    def parse_css(self, compiler: 'Compiler' = None) -> str:
        return ''.join([token.value for token in self.sequence])

    def parse_min_css(self, compiler: 'Compiler' = None) -> str:
        return self.parse_css()


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


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens: List[Token] = tokens
        self.index: int = 0

    @property
    def current_token(self) -> Token | None:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def _type_check_and_advance(self, token_type: TokenType | Iterable[TokenType] | None = None):
        if (token_type is None or self.current_token.type == token_type or
                (isinstance(token_type, Iterable) and self.current_token.type in token_type)):
            self.index += 1
        else:
            raise ValueError(f'Expected {token_type}, got {self.current_token}')

    def parse(self) -> RootNode:
        return self._make_root()

    def _make_root(self) -> RootNode:
        statements = []

        while self.current_token.type != TokenType.EOF:
            if self.current_token.type in STYLE_BEGIN:
                statements.append(self._make_style())
            elif self.current_token.type == TokenType.MIXIN:
                statements.append(self._make_mixin_def())

        return RootNode(statements)

    def _make_mixin_def(self) -> MixinDefNode:
        self._type_check_and_advance()
        symbol = self.current_token
        self._type_check_and_advance(TokenType.IDENTIFIER)
        style_body = self._make_style_body()
        return MixinDefNode(symbol, style_body)

    def _make_style(self, parent_selector: SelectorNode = None) -> StyleNode:
        selector_node = self._make_selector_node(parent_selector)
        mixin_list = None
        if self.current_token.type == TokenType.USING:
            self._type_check_and_advance()
            mixin_list = self._make_identifier_list_node()

        body_node = self._make_style_body(selector_node)
        style = StyleNode(selector_node, body_node, mixin_list)

        return style

    def _make_style_body(self, selector: SelectorNode = None) -> StyleBodyNode:
        body = StyleBodyNode([], [])
        self._type_check_and_advance(TokenType.CURLY_L)
        while self.current_token.type != TokenType.CURLY_R:
            if self.current_token.type == TokenType.CSS_PROPERTY:
                body.property_nodes.append(self._make_property_node())
            elif self.current_token.type in COMBINATORS:
                child_style = self._make_style(parent_selector=selector)
                body.children_style_nodes.append(child_style)
            elif self.current_token.type in STYLE_BEGIN:
                child_style = self._make_style(parent_selector=selector)
                body.children_style_nodes.append(child_style)
        self._type_check_and_advance(TokenType.CURLY_R)
        return body

    def _make_property_node(self) -> PropertyNode:
        prop = self.current_token
        self._type_check_and_advance(TokenType.CSS_PROPERTY)
        self._type_check_and_advance(TokenType.SINGLE_COLON)
        prop_val = self.current_token
        self._type_check_and_advance(TokenType.CSS_PROPERTY_VALUE)
        self._type_check_and_advance(TokenType.LINE_END)
        return PropertyNode(prop, prop_val)

    def _make_selector_node(self, parent_selector: SelectorNode | None) -> SelectorNode:
        single_selector_nodes = [self._make_single_selector_node()]
        while self.current_token.type == TokenType.COMMA:
            self._type_check_and_advance(TokenType.COMMA)
            single_selector_nodes.append(self._make_single_selector_node())
        return SelectorNode(single_selector_nodes, parent_selector)

    def _make_single_selector_node(self) -> SingleSelectorNode:
        parent_combinator = None
        if self.current_token.type in COMBINATORS:  # starts with a combinator, meaning it is nested
            parent_combinator = self.current_token
            self._type_check_and_advance()

        first_node = self._make_selector_sequence_node()
        pairs = []
        while self.current_token.type in COMBINATORS:
            combinator = self.current_token
            self._type_check_and_advance()
            selector_sequence_node = self._make_selector_sequence_node()
            pairs.append((combinator, selector_sequence_node))

        pseudo_class_identifier = pseudo_element_identifier = None

        if self.current_token.type == TokenType.SINGLE_COLON:
            self._type_check_and_advance()
            pseudo_class_identifier = self.current_token
            self._type_check_and_advance(TokenType.IDENTIFIER)

        if self.current_token.type == TokenType.PSEUDO_ELEMENT:
            self._type_check_and_advance()
            pseudo_element_identifier = self.current_token
            self._type_check_and_advance(TokenType.IDENTIFIER)

        attr_selectors = []
        while self.current_token.type == TokenType.SQUARE_L:
            attr_selectors.append(self._make_attribute_selector_node())

        return SingleSelectorNode(first_node, pairs, parent_combinator, pseudo_class_identifier,
                                  pseudo_element_identifier, attr_selectors)

    def _make_attribute_selector_node(self) -> AttributeSelectorNode:
        self._type_check_and_advance(TokenType.SQUARE_L)
        attr = self.current_token
        self._type_check_and_advance(TokenType.IDENTIFIER)
        op = self.current_token
        self._type_check_and_advance(ATTRIBUTE_OPERATORS)
        val = self.current_token
        self._type_check_and_advance((TokenType.STRING, TokenType.IDENTIFIER))
        self._type_check_and_advance(TokenType.SQUARE_R)
        return AttributeSelectorNode(attr, op, val)

    def _make_selector_sequence_node(self) -> SelectorSequenceNode:
        tokens = []
        while self.current_token.type in STYLE_BEGIN + [TokenType.IDENTIFIER]:
            tokens.append(self.current_token)
            self._type_check_and_advance()

        return SelectorSequenceNode(tokens)

    def _make_identifier_list_node(self) -> IdentifierListNode:
        identifiers = [self.current_token]
        self._type_check_and_advance(TokenType.IDENTIFIER)
        while self.current_token.type == TokenType.COMMA:
            self._type_check_and_advance()
            identifiers.append(self.current_token)
            self._type_check_and_advance(TokenType.IDENTIFIER)
        return IdentifierListNode(identifiers)
