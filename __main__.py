from superss import Lexer, Parser, Compiler

with open('examples/1.sss') as f:
    lexer = Lexer(f.read())
    print('*** TOKENS ***\n' + '\n'.join([str(token) for token in lexer.tokens]) + '\n\n')

    parser = Parser(lexer.tokens)
    root = parser.parse()

    print('*** ROOT NODE ***\n', root.statements, '\n\n')

    compiler = Compiler(root)

    print('*** CSS ***\n' + compiler.compile_css(minified=False) + '\n\n')
    print('*** COMPACT CSS ***\n' + compiler.compile_css())
