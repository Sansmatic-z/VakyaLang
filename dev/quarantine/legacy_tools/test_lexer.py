import sys
sys.path.insert(0, ".")
from runtime.src.lexer import Lexer
lexer = Lexer('समय_प्रबंधक.प्रतीक्षा(प्रतीक्षा_समय)')
tokens = lexer.tokenize()
for t in lexer.tokens:
    print(t.type, t.value)
