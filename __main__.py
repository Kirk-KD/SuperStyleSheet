from src.superss import Lexer, Parser, Compiler

with open('src/examples/1.sss') as f:
    lexer = Lexer(f.read())

    lexer.parse_tokens()
    print('*** TOKENS ***\n' + '\n'.join([str(token) for token in lexer.tokens]) + '\n\n')

    parser = Parser(lexer.tokens)
    root = parser.parse()
    compiler = Compiler(root)

    print('*** CSS ***\n' + compiler.compile_css(minified=False) + '\n\n')
    print('*** COMPACT CSS ***\n' + compiler.compile_css())
