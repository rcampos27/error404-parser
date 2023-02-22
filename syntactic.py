from grammar import Grammar
from analisador import Parser
tokens = []

with open('lexems.txt') as file:
    while True:
        line = file.readline()
        if not line: break

        elements = line.split('\t')
        elements[1] = elements[1].strip('\n')
        tokens.append((elements[0], elements[1]))
# tokens.reverse()

# print('\n\nLista Inicial')
# for i, t in enumerate(tokens):
#     print(f'{i} - {t[1]}')

grammar_text = open("grammar.txt", "r")
g = Grammar(grammar_text.read())
parser = Parser(g)
results, errors = parser.parse(tokens)
parser.print_LR_parser(results, errors)

