from grammar import Grammar
import operator as op
 

class Parser:
    def __init__(self, G):
        self.G_aug = Grammar(f"{G.start}' -> {G.start}\n{G.grammar_str}")
        self.max_G_prime_len = len(max(self.G_aug.grammar, key=len))
        self.G_indexed = []

        for head, bodies in self.G_aug.grammar.items():
            for body in bodies:
                self.G_indexed.append([head, body])

        self.first, self.follow = self.firstFollow()
        self.C = self.items(self.G_aug)
        self.action = list(self.G_aug.terminals) + ['$']  # parte 1 tabela
        self.goto = list(self.G_aug.nonterminals -
                         {self.G_aug.start})  # parte 2 tabela
        self.parse_table_symbols = self.action + self.goto  # tabela action/go-to
        self.parse_table = self.createTable()

    def firstFollow(self):
        def union(set_1, set_2):
            set_1_len = len(set_1)
            set_1 |= set_2
            return set_1_len != len(set_1)

        first = {symbol: set() for symbol in self.G_aug.symbols}
        # R1 a -> O first de um não terminal é ele mesmo
        first.update((terminal, {terminal})
                     for terminal in self.G_aug.terminals)
        follow = {symbol: set() for symbol in self.G_aug.nonterminals}
        follow[self.G_aug.start].add('$')  # R1 -> follow(S) contém $

        while True:
            updated = False

            for head, bodies in self.G_aug.grammar.items():
                for body in bodies:
                    for symbol in body:
                        # R3 -> Se X -> YZW, first(X) contém first(Y) - ^...
                        if symbol != '^':
                            updated |= union(
                                first[head], first[symbol] - set('^'))

                            if '^' not in first[symbol]:
                                break
                        else:
                            updated |= union(first[head], set('^'))
                    else:
                        # R2 -> Se X -> ^, então ^ pertence ao first(X)
                        updated |= union(first[head], set('^'))

                    aux = follow[head]
                    for symbol in reversed(body):
                        if symbol == '^':
                            continue  # ^ não pertence ao follow
                        # R3 -> Se A -> aX ou A -> aXB, com B -> ^, follow(A) faz parte de follow(X)
                        if symbol in follow:
                            updated |= union(follow[symbol], aux - set('^'))
                        # R2 -> Se exite A -> aXB, first(B) - ^ pertence ao follow(X)
                        if '^' in first[symbol]:
                            aux = aux | first[symbol]
                        else:
                            aux = first[symbol]

            if not updated:
                return first, follow

    def fechamento(self, I):
        J = I

        while True:
            item_len = len(J)

            for head, bodies in J.copy().items():
                for body in bodies.copy():
                    # Se o ponto não estiver na última posição ( != A -> aB. ), avança o ponto
                    if '.' in body[:-1]:
                        symbol_after_dot = body[body.index('.') + 1]

                        # Se A -> a.Bb estiver em fechamento(I), adicionar produções derivadas de B (B -> ?)
                        if symbol_after_dot in self.G_aug.nonterminals:
                            # Seleciona o lado direito das produções B -> ? e adiciona B -> .? ao fechamento
                            for G_body in self.G_aug.grammar[symbol_after_dot]:
                                J.setdefault(symbol_after_dot, set()).add(
                                    ('.',) if G_body == ('^',) else ('.',) + G_body)

            if item_len == len(J):
                return J

    def desvio(self, I, X):
        desvio = {}
        for head, bodies in I.items():
            for body in bodies:
                if '.' in body[:-1]:
                    dot_pos = body.index('.')

                    # Mover ponto para direita em todos os itens de I onde o ponto precede X
                    if body[dot_pos + 1] == X:
                        # [A -> .?] => [A -> ?.]
                        replaced_dot_body = body[:dot_pos] + \
                            (X, '.') + body[dot_pos + 2:]

                        # Calcular o fechamento deste conjunto de itens
                        for C_head, C_bodies in self.fechamento({head: {replaced_dot_body}}).items():
                            desvio.setdefault(C_head, set()).update(C_bodies)

        return desvio

    def items(self, G_aug):
        # Calcula o fechamento, a partir de S' -> S
        C = [self.fechamento({G_aug.start: {('.', G_aug.start[:-1])}})]
        while True:
            item_len = len(C)

            for I in C.copy():  # para cada conjunto de itens I em C e
                for X in G_aug.symbols:  # cada símbolo gramatical X tal que:
                    desvio = self.desvio(I, X)

                    # desvio(I,X) não seja vazio e não esteja em C incluir desvio(I,X) a C
                    if desvio and desvio not in C:
                        C.append(desvio)

            # até que não haja mais conjuntos de itens a serem incluídos a C
            if item_len == len(C):
                return C

    def createTable(self):
        table = {r: {c: '' for c in self.parse_table_symbols}
                 for r in range(len(self.C))}  # Cria tabela com dimensões C x símbolos

        for i, I in enumerate(self.C):
            for head, bodies in I.items():
                for body in bodies:
                    if '.' in body[:-1]:
                        a = body[body.index('.') + 1]

                        # Aqui a é terminal. Se A -> x.ay estiver em Ii e desvio(Ii,a)=Ij,
                        if a in self.G_aug.terminals:
                            # s = shift; {index} = j
                            s = f'S{self.C.index(self.desvio(I, a))}'

                            if s not in table[i][a]:
                                if 'R' in table[i][a]:
                                    table[i][a] += '/'

                                # então estabelecer ação[i,a] em “empilha j”. //R1
                                table[i][a] += s

                    # Aqui A é diferente de S’. Se A -> α. estiver em Ii,
                    elif body[-1] == '.' and head != self.G_aug.start:
                        for j, (G_head, G_body) in enumerate(self.G_indexed):
                            if G_head == head and (G_body == body[:-1] or G_body == ('^',) and body == ('.',)):
                                # então estabelecer ação[i,a] em “reduzir através de A → α” para todo a em Follow(A). //R2
                                for follow in self.follow[head]:
                                    if table[i][follow]:
                                        table[i][follow] += '/'

                                    table[i][follow] += f'R{j}'

                                break

                    # Se S’ → S• estiver em Ii, então estabelecer ação[i,$] igual a “aceitar”. //R3
                    else:
                        table[i]['$'] = 'acc'

            # As transições de desvio para o estado i são construídos pra todos os não-terminais A usando a regra: se desvio(Ii,A)=Ij, então desvio[i,A]=j //R4
            for A in self.G_aug.nonterminals:
                j = self.desvio(I, A)

                if j in self.C:
                    table[i][A] = self.C.index(j)

        return table

    def parse(self, tokens):
        w = ' '.join(t[0] for t in tokens)
        buffer = w.split()
        d = ' '.join(t[1] for t in tokens)
        lexval = d.split()
        lex = []
        tipos = []
        val = []

        arit_ops = {
            '+' : op.add,
            '-' : op.sub,
            '*' : op.mul,
            '/' : op.truediv,
            '%' : op.mod,
            'or': op.or_,
            'and': op.and_,
            'not': op.not_
        }
        rel_ops = {
            '>=': op.ge,
            '>': op.gt,
            '<=': op.le,
            '<': op.lt,
            '=': op.eq,
            '!=': op.ne
        }

        ip = 0  # Fazer ip apontar para o primeiro símbolo de w$;
        stack = ['0']  # Seja s o estado do topo da pilha
        # e a o símbolo apontado por ip; se ação[s,a] = empilhar s’
        a = buffer[ip]
        errors = []
        results = {
            'step': [''],
            'stack': ['PILHA'] + stack,
            'input': ['ENTRADA'],
            'action': ['AÇÃO'],
        }

        step = 0
        while True:
            s = int(stack[-1])
            step += 1
            results['step'].append(f'({step})')
            results['input'].append(' '.join(buffer[ip:]))
            if '/' in self.parse_table[s][a]: 
                symbols = self.parse_table[s][a]
                print(symbols)
                action = 'reduz' if symbols.count('R') > 1 else 'empilha'
                results['action'].append(f'Erro {len(errors)}')
                errors.append(f'Conflito {action}-reduz. Analisando símbolo {a} no estado {s}. Estado pode: {symbols}.')

                selected = symbols.split('/')[0]
                print(selected)
                self.parse_table[s][a] = selected
                continue 

    
            elif self.parse_table[s][a] == '':                
                simbolos = set()
                reduction = ''
                reduces = False
                for sym in self.parse_table[s]:
                    symbol = self.parse_table[s][sym]
                    if symbol != '':
                        simbolos.add(sym)
                    if not reduces and str(symbol).startswith('R'):
                        reduction = self.parse_table[s][sym]
                        reduces = True

                results['stack'].append(' '.join(stack))
                results['action'].append(f'Erro {len(errors)}')
                errors.append(f"Símbolo inesperado '{a}'. Esperava-se {simbolos}")

                # Linhas que contém reduções: Células em branco são preenchidas com reduções
                if reduces:
                    self.parse_table[s][a] = reduction
                else:  # Demais células: Chamadas a rotinas de tratamento de erros
                    ip += 1
                    if ip < len(buffer):
                        a = buffer[ip]
                    else: break
                continue

            # se ação[s,a] = empilhar s’
            
            if self.parse_table[s][a].startswith('S'):
                # ? empilhar a e s’ no topo da pilha; avançar ip para o próximo símbolo de entrada;
                results['action'].append('Shift')
                stack.append(a)
                stack.append(self.parse_table[s][a][1:])
                results['stack'].append(' '.join(stack))
                lex.append(lexval[ip])
                tipos.append('')
                val.append('')

                ip += 1
                if ip < len(buffer):
                    a = buffer[ip]
                else: break

            # senão se ação[s,a] = reduzir A -> ß desempilhar 2*|ß|;
            elif self.parse_table[s][a].startswith('R'):
                head, body = self.G_indexed[int(self.parse_table[s][a][1:])]
                rule = int(self.parse_table[s][a][1:])
                results['action'].append(
                    f'Reduz com #{rule}: {head} -> {" ".join(body)}')

#TODO Dar 'pop' nas pilhas depois do processamento
                if body != ('^',):
                    stack = stack[:-2*len(body)]
                    if (rule == 20):                    
                        val.append(lexval[ip])
                        tipos.append("string")
                        lex.append(lexval[ip])
                    elif (rule == 21):
                        if tipos[-3] == tipos[-1]:
                            val[-3] = val[-1]
                            lex = lex[:-1]
                            tipos = tipos[:-1]
                            val = val[:-1]
                        else: print(f'Erro: Tipo não compatível (1)')
                    elif (rule == 22):
                        print(lex[-2])
                        if lex[-2] == tipos[-1]: 
                            simbolos.append(lex[-1], tipos[-1], val[-1]) 
                            lex = lex[:-2]
                            tipos = tipos[:-2]
                            val = val[:-2]
                        else: print(f'Erro: Tipo não compatível (2)')

                        print(rule)
                    elif (rule == 23 or rule == 24):
                        val.append(lexval[ip])
                        tipos.append("int")
                        lex.append(lexval[ip])
                    elif (rule == 25 or rule == 26):
                        val.append(lexval[ip])
                        tipos.append("float")
                        lex.append(lexval[ip])
                    elif (rule == 43 or rule == 44 or rule == 45 or rule == 46):
                        if tipos[-1] == tipos[-3]: 
                            print(lex[-2])
                            if tipos[-3] == "int":
                                res = rel_ops[lex[-2]](int(val[-1]), int(val[-3]))
                            elif tipos[-3] == "float":
                                res = rel_ops[lex[-2]](float(val[-1]), float(val[-3]))
                            else: 
                                res = rel_ops[lex[-2]](bool(val[-1]), bool(val[-3]))
                                
                            val = val[:-3]
                            val.append(res)
                            tipos = tipos[:-2]
                    elif(rule == 47 or rule == 49):
                        if tipos[-1] == tipos[-3]: 
                            print(lex[-2])
                            if tipos[-3] == "int":
                                res = arit_ops[lex[-2]](int(val[-1]), int(val[-3]))
                            elif tipos[-3] == "float":
                                res = arit_ops[lex[-2]](float(val[-1]), float(val[-3]))
                            else: 
                                print(lex[-1])
                                print(lex[-2])
                                print(lex[-3])
                                res = arit_ops[lex[-2]](bool(val[-1]), bool(val[-3]))
                                
                            val = val[:-3]
                            val.append(res)
                            tipos = tipos[:-2]
                    elif (rule == 51 or rule == 53):
                        print(rule)
                    elif (rule == 52):
                        print(rule)
                    elif (rule == 54):
                        print(rule)
                    elif (rule == 56):
                        el = ''
                        for simb in simbolos:
                            if simb['nome'] == lexval[ip]:
                                el = simb
                                break
                        lex.append(el['val'])
                        tipos.append(el['tipo'])
                        val.append(el['val'])
                    elif (rule == 59):
                        print(rule)
                    elif (rule == 60):
                        print(rule)
                    elif (rule == 61):
                        print(rule)

                stack.append(str(head))
                # seja s’ o estado agora no topo da pilha; empilhar A e em seguida desvio[s’,A];
                stack.append(str(self.parse_table[int(stack[-2])][head]))
                results['stack'].append(' '.join(stack))

            # senão se ação[s,a] = aceitar; retorna "Aceita"
            elif self.parse_table[s][a] == 'acc':
                results['action'].append('Aceita')
                for i, el in enumerate(self.G_indexed):
                    print(f'{i}: {el}')
                break

        return results, errors

    def writeToResult(self, results, errors):
        file = open('syntactic_result.txt', 'w')
        def print_line():
            file.write(f'{"".join(["-" + ("-" * (max_len + 2)) for max_len in max_lens.values()])}-')
            file.write('\n')

        max_lens = {key: max(len(value) for value in results[key]) for key in results}
        justs = {
            'step': '>',
            'stack': '',
            'input': '>',
            'action': ''
        }
        print_line()
        file.write(''.join(
            [f'| {history[0]:^{max_len}} ' for history, max_len in zip(results.values(), max_lens.values())]) + '|\n')
        print_line()
        for i, step in enumerate(results['step'][:-1], 1):
            file.write(''.join([f'| {history[i]:{just}{max_len}} ' for history, just, max_len in
                           zip(results.values(), justs.values(), max_lens.values())]) + '|\n')

        print_line()
        for i, e in enumerate(errors):
            file.write(f'({i}) - {e} \n')

