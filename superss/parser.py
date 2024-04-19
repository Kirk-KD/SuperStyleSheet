from typing import List, Tuple, TYPE_CHECKING
from collections.abc import Iterable

from superss import Token, TokenType, STYLE_BEGIN, COMBINATORS, ATTRIBUTE_OPERATORS, IDENTIFIERS
from superss.nodes import *

if TYPE_CHECKING:
    from superss import Compiler


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
            if self.current_token.type in STYLE_BEGIN + [TokenType.SQUARE_L, TokenType.SINGLE_COLON]:
                statements.append(self._make_style())
            elif self.current_token.type == TokenType.MIXIN:
                statements.append(self._make_mixin_def())
            elif self.current_token.type == TokenType.ALIAS:
                statements.append(self._make_alias_def())

        return RootNode(statements)

    def _make_alias_def(self):
        self._type_check_and_advance(TokenType.ALIAS)
        symbol = self.current_token
        self._type_check_and_advance(IDENTIFIERS)
        self._type_check_and_advance(TokenType.AS)
        selector = self._make_selector_node(None)
        return AliasDefNode(symbol, selector)

    def _make_mixin_def(self) -> MixinDefNode:
        self._type_check_and_advance()
        symbol = self.current_token
        self._type_check_and_advance(IDENTIFIERS)
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
        while self.current_token.type in COMBINATORS + [TokenType.SPACE]:
            combinator = self.current_token
            self._type_check_and_advance()
            selector_sequence_node = self._make_selector_sequence_node()
            pairs.append((combinator, selector_sequence_node))

        pseudo_element = None
        if self.current_token.type == TokenType.PSEUDO_ELEMENT:
            pseudo_element = self._make_pseudo_element_node()

        return SingleSelectorNode(first_node, pairs, parent_combinator, pseudo_element)

    def _make_attribute_selector_node(self) -> AttributeSelectorNode:
        self._type_check_and_advance(TokenType.SQUARE_L)
        attr = self.current_token
        self._type_check_and_advance(TokenType.IDENTIFIER)

        op = val = None
        if self.current_token.type in ATTRIBUTE_OPERATORS:
            op = self.current_token
            self._type_check_and_advance(ATTRIBUTE_OPERATORS)
            val = self.current_token
            self._type_check_and_advance((TokenType.STRING, TokenType.IDENTIFIER))

        self._type_check_and_advance(TokenType.SQUARE_R)
        return AttributeSelectorNode(attr, op, val)

    def _make_selector_sequence_node(self) -> SelectorSequenceNode:
        tokens = []
        while self.current_token.type in STYLE_BEGIN + IDENTIFIERS:
            tokens.append(self.current_token)
            self._type_check_and_advance()

        pseudo_class_nodes = []
        attr_selectors = []

        while self.current_token.type == TokenType.SQUARE_L:
            attr_selectors.append(self._make_attribute_selector_node())

        while self.current_token.type == TokenType.SINGLE_COLON:
            pseudo_class_nodes.append(self._make_pseudo_class_node())

        return SelectorSequenceNode(tokens, attr_selectors, pseudo_class_nodes)

    def _make_pseudo_class_node(self) -> PseudoClassNode:
        self._type_check_and_advance(TokenType.SINGLE_COLON)
        identifier = self.current_token
        self._type_check_and_advance(TokenType.IDENTIFIER)
        attr_selectors = []
        if self.current_token.type == TokenType.SQUARE_L:
            attr_selectors.append(self._make_attribute_selector_node())
        return PseudoClassNode(identifier, attr_selectors)

    def _make_pseudo_element_node(self) -> PseudoElementNode:
        self._type_check_and_advance(TokenType.PSEUDO_ELEMENT)
        identifier = self.current_token
        self._type_check_and_advance(TokenType.IDENTIFIER)
        attr_selectors = []
        if self.current_token.type == TokenType.SQUARE_L:
            attr_selectors.append(self._make_attribute_selector_node())
        return PseudoElementNode(identifier, attr_selectors)

    def _make_identifier_list_node(self) -> IdentifierListNode:
        identifiers = [self.current_token]
        self._type_check_and_advance(IDENTIFIERS)
        while self.current_token.type == TokenType.COMMA:
            self._type_check_and_advance()
            identifiers.append(self.current_token)
            self._type_check_and_advance(TokenType.IDENTIFIER)
        return IdentifierListNode(identifiers)
