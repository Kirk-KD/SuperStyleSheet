import unittest
from typing import List, Tuple, Any

from superss import Lexer, TokenType


class TestTokens(unittest.TestCase):
    def _test_types(self, string: str, token_types: List[TokenType]):
        lexer = Lexer(string, keep_eof=False)
        self.assertEqual(lexer.token_types, token_types)

    def _test_tokens(self, string: str, tokens: List[Tuple[TokenType, Any]]):
        lexer = Lexer(string, keep_eof=False)
        self.assertEqual(lexer.token_pairs, tokens)

    def _test_one(self, string: str, type_: TokenType, value: Any):
        lexer = Lexer(string, keep_eof=False)
        self.assertEqual(len(lexer.tokens), 1, 'More than one token made.')
        self.assertEqual(lexer.tokens[0].type, type_)
        self.assertEqual(lexer.tokens[0].value, value)

    def test_misc(self):
        self._test_types(', ;',
                         [TokenType.COMMA, TokenType.LINE_END])
        self._test_one('"Test Sting"', TokenType.STRING, 'Test Sting')

    def test_brackets(self):
        self._test_types('( ) [ ] { }',
                         [TokenType.PAREN_L, TokenType.PAREN_R, TokenType.SQUARE_L, TokenType.SQUARE_R,
                          TokenType.CURLY_L, TokenType.CURLY_R])

    def test_selector(self):
        self._test_types('. # *',
                         [TokenType.CLASS_PREFIX, TokenType.ID_PREFIX, TokenType.STAR])

    def test_combinator(self):
        self._test_types('+ ~ >',
                         [TokenType.AFTER, TokenType.BEFORE, TokenType.CHILD])

    def test_attr_comparison(self):
        self._test_types('= ~= *= |= ^= $=',
                         [TokenType.ATTR_EQUALS,
                          TokenType.ATTR_CONTAINS_WORD,
                          TokenType.ATTR_CONTAINS,
                          TokenType.ATTR_STARTS_WITH_WORD,
                          TokenType.ATTR_STARTS_WITH,
                          TokenType.ATTR_ENDS_WITH])

    def test_pseudo(self):
        self._test_types(': ::',
                         [TokenType.SINGLE_COLON, TokenType.PSEUDO_ELEMENT])

    def test_identifier(self):
        self._test_one('test1', TokenType.IDENTIFIER, 'test1')
        self._test_one('test-test_test', TokenType.IDENTIFIER, 'test-test_test')
        self._test_one('_test', TokenType.IDENTIFIER, '_test')
        self._test_one('-test', TokenType.IDENTIFIER, '-test')
        self._test_one('_-_-_-1_-test-_-_-_-_-', TokenType.IDENTIFIER, '_-_-_-1_-test-_-_-_-_-')

    def test_keywords(self):
        self._test_one('h1', TokenType.HTML_ELEMENT, 'h1')
        self._test_one('font-weight', TokenType.CSS_PROPERTY, 'font-weight')
        self._test_tokens('border: 1px solid blue',
                          [(TokenType.CSS_PROPERTY, 'border'),
                           (TokenType.SINGLE_COLON, ':'),
                           (TokenType.CSS_PROPERTY_VALUE, '1px solid blue')])

    def test_reserved(self):
        self._test_types('using mixin alias as',
                         [TokenType.USING,
                          TokenType.MIXIN,
                          TokenType.ALIAS,
                          TokenType.AS])
