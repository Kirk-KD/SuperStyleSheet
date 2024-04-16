import unittest

from superss import Lexer, Parser, Compiler


class TestCompiler(unittest.TestCase):
    def _test_compiler(self, input_string: str, output_string_min: str, output_string_full: str | None = None):
        lexer = Lexer(input_string)
        parser = Parser(lexer.tokens)
        compiler = Compiler(parser.parse())

        self.assertEqual(compiler.compile_css(minified=True), output_string_min, 'Unexpected minified CSS result.')
        if output_string_full is not None:
            self.assertEqual(compiler.compile_css(), output_string_full, 'Unexpected full CSS result.')

    def test_selectors(self):
        self._test_compiler('.my-class {}', '.my-class{}')
        self._test_compiler('.  my-class    {  }', '.my-class{}')
        self._test_compiler('#my-class{  }    ', '#my-class{}')
        self._test_compiler('h1 {}', 'h1{}')
        self._test_compiler('* {}', '*{}')

    def test_selector_list(self):
        self._test_compiler('.my-class,  #my-id    ,   h3,h1{}', '.my-class,#my-id,h3,h1{}')

    def test_selector_combinators(self):
        self._test_compiler('img h2 {}', 'img h2{}')
        self._test_compiler('div> div  >p  {  }', 'div>div>p{}')
        self._test_compiler('div ~ . my-class p> h2 +#test {}', 'div~.my-class p>h2+#test{}')
