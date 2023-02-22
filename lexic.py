reserved = {"when", "if", "else", "for", "while", "default", "is", "true", "false", "write", "read"}
types = {"int", "float", "bool", "string"}


def get_token(str):
    if str == "and" or str == "or" or str == "not":
        token = ("logic_op", str)
    elif str in types:
        token = ("type", str)
    elif str in reserved:
        token = (str, str)
    else:
        token = ("id", str)

    return token


estado = 1
line = 1
tokens = []
errors = []

with open('program.txt') as f:
    while True:
        c = f.read(1)
        if not c:
            break
        if c.isspace():
            if c == '\n':
                line += 1
            continue

        str = ''
        if c.isalpha() or c == '_':
            estado = 2
            while True:
                if c.isalnum() or c == '_':
                    str += c
                    c = f.read(1)
                else:
                    tokens.append(get_token(str))

                    f.seek(f.tell() - 1)
                    estado = 1
                    break
        elif c == "{" or c == "}" or c == "(" or c == ")" or c == ";":
            tokens.append((c, c))
        elif c == "*" or c == "/" or c == "%":
            tokens.append(("arit_op_1", c))
        elif c == "#":
            estado = 6
            while True:
                if c != '\n':
                    str += c
                    c = f.read(1)
                else:
                    tokens.append(("comment", str))

                    f.seek(f.tell() - 1)
                    estado = 1
                    break

        elif c.isnumeric():
            estado = 8
            while estado == 8:
                if c.isnumeric():
                    str += c
                    c = f.read(1)
                elif c == '.':
                    estado = 9
                    str += c
                    c = f.read(1)
                    break
                else:
                    tokens.append(("int", str))

                    f.seek(f.tell() - 1)
                    estado = 1
                    break

            if estado == 9 and not c.isnumeric():
                errors.append((str + c, line))
                estado = 1

            while estado == 9:
                if c.isnumeric():
                    str += c
                    c = f.read(1)
                else:
                    tokens.append(("float", str))

                    f.seek(f.tell() - 1)
                    estado = 1
                    break

        elif c == '+':
            str += c

            c = f.read(1)
            if c == '+':
                str += c
                tokens.append(("inc", str))
            else:
                tokens.append(("arit_op_2", str))
                f.seek(f.tell() - 1)

        elif c == '-':
            str += c

            c = f.read(1)
            if c == '-':
                str += c
                tokens.append(("inc", str))
            elif c.isnumeric():
                estado = 8
                while estado == 8:
                    if c.isnumeric():
                        str += c
                        c = f.read(1)
                    elif c == '.':
                        estado = 9
                        str += c
                        c = f.read(1)
                        break
                    else:
                        tokens.append(("int_sinal", str))

                        f.seek(f.tell() - 1)
                        estado = 1
                        break

                if estado == 9 and not c.isnumeric():
                    errors.append((str + c, line))
                    estado = 1

                while estado == 9:
                    if c.isnumeric():
                        str += c
                        c = f.read(1)
                    else:
                        tokens.append(("float_sinal", str))

                        f.seek(f.tell() - 1)
                        estado = 1
                        break
            else:
                tokens.append(("arit_op_2", str))
                f.seek(f.tell() - 1)

        elif c == '<' or c == '>':
            str += c
            c = f.read(1)

            if c == '=':
                str += c
            tokens.append(("rel_op", str))
        elif c == '=':
            str += c
            c = f.read(1)
            if c == '=':
                str += c
                tokens.append(("rel_op", str))
            else:
                tokens.append(("=", str))
                f.seek(f.tell() - 1)
        elif c == '!':
            str += c
            c = f.read(1)
            if c == '=':
                str += c
                tokens.append(("rel_op", str))
            else:
                errors.append((str + c, line))

        elif c == '"':
            str += c
            c = f.read(1)
            estado = 24

            while True:
                if c == '"':
                    str += c
                    tokens.append(("string", str))
                    estado = 1
                    break
                else:
                    str += c
                    c = f.read(1)
        else:
            errors.append((str + c, line))
            estado = 1

tokens.append(('$', '$'))

lexems = open("lexems.txt", "w")
errors = open("errors.txt", "w")

for token in tokens:
    lexems.write(token[0])
    lexems.write("\t")
    lexems.write(token[1])
    lexems.write('\n')
    print(f"[{token[0]}, {token[1]}]")
for error in errors:
    errors.write(f"Símbolo não reconhecido (Linha {error[1]}): {error[0]}")