import sys, os
sys.path.insert(0, './runtime/src')
from lexer import Lexer
from parser import Parser

source = "चर सूची_१ = [क * २ प्रत्येक चर क अन्तर्गत परास(५)]"
l = Lexer(source)
p = Parser(l.tokenize())
ast = p.parse()
print(ast)
