from enum import Enum
from typing import Any, List, Tuple

from superss.util import load_html_elements, load_css_properties, make_keywords_dict


class TokenType(Enum):
    STAR = '*'
    COMMA = ','
    AFTER = '+'
    BEFORE = '~'
    CHILD = '>'
    ID_PREFIX = '#'
    CLASS_PREFIX = '.'
    SINGLE_COLON = ':'  # also pseudo class
    PSEUDO_ELEMENT = '::'
    ATTR_EQUALS = '='
    ATTR_CONTAINS_WORD = '~='
    ATTR_CONTAINS = '*='
    ATTR_STARTS_WITH_WORD = '|='
    ATTR_STARTS_WITH = '^='
    ATTR_ENDS_WITH = '$='
    LINE_END = ';'

    PAREN_L = '('
    PAREN_R = ')'
    CURLY_L = '{'
    CURLY_R = '}'
    SQUARE_L = '['
    SQUARE_R = ']'

    IDENTIFIER = 'Identifier'
    HTML_ELEMENT = 'HTML Element'
    CSS_PROPERTY = 'CSS Property'

    USING = 'using'
    MIXIN = 'mixin'
    ALIAS = 'alias'
    AS = 'as'

    STRING = 'String'
    EOF = 'End of File'
    CSS_PROPERTY_VALUE = 'CSS Property Value'
    SPACE = 'Space'


KEYWORDS = make_keywords_dict([TokenType.USING, TokenType.MIXIN, TokenType.ALIAS, TokenType.AS])
ELEMENTS = load_html_elements()
PROPERTIES = load_css_properties()
STYLE_BEGIN = [TokenType.HTML_ELEMENT, TokenType.CLASS_PREFIX, TokenType.ID_PREFIX, TokenType.STAR]
COMBINATORS = [TokenType.BEFORE, TokenType.AFTER, TokenType.CHILD]
ATTRIBUTE_OPERATORS = [TokenType.ATTR_EQUALS, TokenType.ATTR_CONTAINS, TokenType.ATTR_CONTAINS_WORD,
                       TokenType.ATTR_STARTS_WITH_WORD, TokenType.ATTR_ENDS_WITH, TokenType.ATTR_STARTS_WITH]
IDENTIFIERS = [TokenType.IDENTIFIER, TokenType.CSS_PROPERTY, TokenType.HTML_ELEMENT]


class Token:
    def __init__(self, type_: TokenType | None, value: Any | None, line: int = None, column: int = None) -> None:
        self.type: TokenType = type_
        self.value: Any = value
        self.line: int = line
        self.column: int = column

    def __str__(self) -> str:
        return f'Token({self.type}: {repr(self.value)}' + (
            f' at {self.line + 1}:{self.column + 1})' if self.line is not None and self.column is not None else ')')

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def is_not_eof(self) -> bool:
        return self.type != TokenType.EOF


class Lexer:
    def __init__(self, text: str, keep_eof: bool = True):
        self.text: str = text
        self.index: int = 0
        self.line: int = 0
        self.column: int = 0
        self.keep_eof: bool = keep_eof

        self.tokens: List[Token] = []
        self.token_types: List[TokenType] = []
        self.token_values: List[Any] = []
        self.token_pairs: List[Tuple[TokenType, Any]] = []
        self._parse_tokens()

    @property
    def current_char(self) -> str:
        return self.text[self.index] if self.index < len(self.text) else None

    @property
    def next_char(self) -> str:
        return self.text[self.index + 1] if self.index + 1 < len(self.text) else None

    def last_token(self, i: int = 0) -> Token:
        return self.tokens[len(self.tokens) - i - 1] if len(self.tokens) - i - 1 >= 0 else None

    def _advance(self) -> None:
        if self.current_char == '\n':
            self.line += 1
            self.column = 0

        self.index += 1
        if self.index < len(self.text):
            self.column += 1

    def _parse_tokens(self):
        self._parse_next_token()
        while len(self.tokens) and self.tokens[-1].is_not_eof:
            self._parse_next_token()

        # TODO better way of determining when to parse SPACE tokens
        cleaned_tokens = []
        for i in range(len(self.tokens)):
            current_token = self.tokens[i]
            if current_token.type == TokenType.SPACE:
                if 0 < i < len(self.tokens):
                    left = self.tokens[i - 1]
                    right = self.tokens[i + 1]
                    if (left.type in (TokenType.HTML_ELEMENT, TokenType.IDENTIFIER, TokenType.STAR, TokenType.SQUARE_R)
                            and right.type in
                            (TokenType.CLASS_PREFIX, TokenType.ID_PREFIX, TokenType.HTML_ELEMENT, TokenType.STAR)):
                        cleaned_tokens.append(current_token)
            elif self.keep_eof or current_token.type != TokenType.EOF:
                cleaned_tokens.append(current_token)

        self.tokens = cleaned_tokens
        for token in self.tokens:
            self.token_types.append(token.type)
            self.token_values.append(token.value)
            self.token_pairs.append((token.type, token.value))

    def _parse_next_token(self) -> None:
        while self.current_char is not None:
            if self.current_char.isspace():
                self._skip_space()
                continue

            if is_identifier_start(self.current_char):
                self.tokens.append(self._make_identifier())
                continue
            if is_string_start(self.current_char):
                self.tokens.append(self._make_string())
                continue

            # double character tokens
            if self.current_char == '~' and self.next_char == '=':
                self.tokens.append(Token(TokenType.ATTR_CONTAINS_WORD, '~=', self.line, self.column))
                self._advance()
            elif self.current_char == '*' and self.next_char == '=':
                self.tokens.append(Token(TokenType.ATTR_CONTAINS, '*=', self.line, self.column))
                self._advance()
            elif self.current_char == '|' and self.next_char == '=':
                self.tokens.append(Token(TokenType.ATTR_STARTS_WITH_WORD, '|=', self.line, self.column))
                self._advance()
            elif self.current_char == '^' and self.next_char == '=':
                self.tokens.append(Token(TokenType.ATTR_STARTS_WITH, '^=', self.line, self.column))
                self._advance()
            elif self.current_char == '$' and self.next_char == '=':
                self.tokens.append(Token(TokenType.ATTR_ENDS_WITH, '$=', self.line, self.column))
                self._advance()
            elif self.current_char == ':' and self.next_char == ':':
                self.tokens.append(Token(TokenType.PSEUDO_ELEMENT, '::', self.line, self.column))
                self._advance()

            # single character tokens
            elif self.current_char == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.column))
            elif self.current_char == '.':
                self.tokens.append(Token(TokenType.CLASS_PREFIX, '.', self.line, self.column))
            elif self.current_char == '#':
                self.tokens.append(Token(TokenType.ID_PREFIX, '#', self.line, self.column))
            elif self.current_char == '*':
                self.tokens.append(Token(TokenType.STAR, '*', self.line, self.column))
            elif self.current_char == '+':
                self.tokens.append(Token(TokenType.AFTER, '+', self.line, self.column))
            elif self.current_char == '~':
                self.tokens.append(Token(TokenType.BEFORE, '~', self.line, self.column))
            elif self.current_char == '>':
                self.tokens.append(Token(TokenType.CHILD, '>', self.line, self.column))
            elif self.current_char == ':':
                is_css_prop_value = self.last_token() is not None and self.last_token().type == TokenType.CSS_PROPERTY
                self.tokens.append(Token(TokenType.SINGLE_COLON, ':', self.line, self.column))
                if is_css_prop_value:
                    self._advance()
                    self.tokens.append(self._make_css_property_value())
            elif self.current_char == '=':
                self.tokens.append(Token(TokenType.ATTR_EQUALS, '=', self.line, self.column))
            elif self.current_char == ';':
                self.tokens.append(Token(TokenType.LINE_END, ';', self.line, self.column))
            elif self.current_char == '(':
                self.tokens.append(Token(TokenType.PAREN_L, '(', self.line, self.column))
            elif self.current_char == ')':
                self.tokens.append(Token(TokenType.PAREN_R, ')', self.line, self.column))
            elif self.current_char == '{':
                self.tokens.append(Token(TokenType.CURLY_L, '{', self.line, self.column))
            elif self.current_char == '}':
                self.tokens.append(Token(TokenType.CURLY_R, '}', self.line, self.column))
            elif self.current_char == '[':
                self.tokens.append(Token(TokenType.SQUARE_L, '[', self.line, self.column))
            elif self.current_char == ']':
                self.tokens.append(Token(TokenType.SQUARE_R, ']', self.line, self.column))

            self._advance()

        self.tokens.append(Token(TokenType.EOF, None))

    def _skip_space(self) -> None:
        if len(self.tokens):
            self.tokens.append(Token(TokenType.SPACE, ' ', self.line, self.column))

        while self.current_char is not None and self.current_char.isspace():
            self._advance()

    def _make_identifier(self) -> Token:
        token = Token(None, None, self.line, self.column)
        value = ''
        while self.current_char is not None and is_identifier(self.current_char):
            value += self.current_char
            self._advance()

        if value in ELEMENTS:
            token.type = TokenType.HTML_ELEMENT
            token.value = value.lower()
        elif value in PROPERTIES:
            token.type = TokenType.CSS_PROPERTY
            token.value = value.lower()
        elif value in KEYWORDS:
            token.type = KEYWORDS[value]
            token.value = value
        else:
            token.type = TokenType.IDENTIFIER
            token.value = value

        return token

    def _make_string(self) -> Token:
        value = self.current_char
        closing = self.current_char

        self._advance()
        while self.current_char != closing:
            if self.current_char is None:
                raise SyntaxError

            value += self.current_char
            self._advance()
        self._advance()

        return Token(TokenType.STRING, value.strip(closing), self.line, self.column)

    def _make_css_property_value(self) -> Token:
        value = ''
        while self.current_char is not None and self.current_char not in ';}\n':
            value += self.current_char
            self._advance()
        self.index -= 1
        return Token(TokenType.CSS_PROPERTY_VALUE, value.strip(), self.line, self.column)


def is_identifier_start(c: str) -> bool:
    return c.isalpha() or c in '_-'  # TODO differentiate from double hyphen for variable definition


def is_identifier(c: str) -> bool:
    return c.isalnum() or c in '_-'


def is_string_start(c: str) -> bool:
    return c in ['"', "'"]
