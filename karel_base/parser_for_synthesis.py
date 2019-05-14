from __future__ import print_function

from karel_base.parser_base import dummy, get_hash, parser_prompt, Parser, AST

from karel_base.utils import debug

from karel_base.utils import beautify


class KarelForSynthesisParser(Parser):

    tokens = [
            'DEF', 'RUN', 
            'M_LBRACE', 'M_RBRACE', 'C_LBRACE', 'C_RBRACE', 'R_LBRACE', 'R_RBRACE',
            'W_LBRACE', 'W_RBRACE', 'I_LBRACE', 'I_RBRACE', 'E_LBRACE', 'E_RBRACE',
            'INT', #'NEWLINE', 'SEMI', 
            'WHILE', 'REPEAT',
            'IF', 'IFELSE', 'ELSE',
            'FRONT_IS_CLEAR', 'LEFT_IS_CLEAR', 'RIGHT_IS_CLEAR',
            'MARKERS_PRESENT', 'NO_MARKERS_PRESENT', 'NOT',
            'MOVE', 'TURN_RIGHT', 'TURN_LEFT',
            'PICK_MARKER', 'PUT_MARKER',
    ]

    t_ignore =' \t\n'

    t_M_LBRACE = 'm\('
    t_M_RBRACE = 'm\)'

    t_C_LBRACE = 'c\('
    t_C_RBRACE = 'c\)'

    t_R_LBRACE = 'r\('
    t_R_RBRACE = 'r\)'

    t_W_LBRACE = 'w\('
    t_W_RBRACE = 'w\)'

    t_I_LBRACE = 'i\('
    t_I_RBRACE = 'i\)'

    t_E_LBRACE = 'e\('
    t_E_RBRACE = 'e\)'

    t_DEF = 'DEF'
    t_RUN = 'run'
    t_WHILE = 'WHILE'
    t_REPEAT = 'REPEAT'
    t_IF = 'IF'
    t_IFELSE = 'IFELSE'
    t_ELSE = 'ELSE'
    t_NOT = 'not'

    t_FRONT_IS_CLEAR = 'frontIsClear'
    t_LEFT_IS_CLEAR = 'leftIsClear'
    t_RIGHT_IS_CLEAR = 'rightIsClear'
    t_MARKERS_PRESENT = 'markersPresent'
    t_NO_MARKERS_PRESENT = 'noMarkersPresent'


    conditional_functions = [
            t_FRONT_IS_CLEAR, t_LEFT_IS_CLEAR, t_RIGHT_IS_CLEAR,
            t_MARKERS_PRESENT, t_NO_MARKERS_PRESENT,
    ]

    t_MOVE = 'move'
    t_TURN_RIGHT = 'turnRight'
    t_TURN_LEFT = 'turnLeft'
    t_PICK_MARKER = 'pickMarker'
    t_PUT_MARKER = 'putMarker'


    action_functions = [
            t_MOVE,
            t_TURN_RIGHT, t_TURN_LEFT,
            t_PICK_MARKER, t_PUT_MARKER,
    ]

    #########
    # lexer
    #########

    INT_PREFIX = 'R='

    def __init__(self, parse_only=False, *args, **kwargs):
        super(KarelForSynthesisParser, self).__init__(*args, **kwargs)
        self.parse_only =  parse_only

    def t_INT(self, t):
        r'R=\d+'

        value = int(t.value.replace(self.INT_PREFIX, ''))
        if not (self.min_int <= value <= self.max_int):
            raise Exception(" [!] Out of range ({} ~ {}): `{}`". \
                    format(self.min_int, self.max_int, value))

        t.value = value
        return t

    def random_INT(self):
        return "{}{}".format(
                self.INT_PREFIX,
                self.rng.randint(self.min_int, self.max_int + 1))

    def t_error(self, t):
        print("Illegal character %s" % repr(t.value[0]))
        t.lexer.skip(1)


    #########
    # parser
    #########

    def p_prog(self, p):
        '''prog : DEF RUN M_LBRACE stmt M_RBRACE'''
        # debug(p.slice[4].slice)
        stmt = p[4]

        @self.callout
        def fn():
            return stmt()
        p[0] = fn
        # debug(p.slice[0], ' -> ', p.slice[4])
        self.actions.append((p.slice[0], (p.slice[4], 'NT')))
        # debug(p.slice[0])

    def p_stmt(self, p):
        '''stmt : while
                | repeat
                | stmt_stmt
                | action
                | if
                | ifelse
        '''
        function = p[1]

        @self.callout
        def fn():
            r = function()
            # debug(p.slice[0], ' -> ', p.slice[1])
            return r
        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[1], 'NT')))

    def p_stmt_stmt(self, p):
        '''stmt_stmt : stmt stmt
        '''
        stmt1, stmt2 = p[1], p[2]

        @self.callout
        def fn():
            # debug(p.slice[0], ' -> ', p.slice[1], ' ', p.slice[2])
            stmt1(); stmt2();
        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[1], 'NT'), (p.slice[2], 'NT')))

    def p_if(self, p):
        '''if : IF C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE
        '''
        cond, stmt = p[3], p[6]

        hit_info = self.hit_info
        if hit_info is not None:
            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                if cond():
                    hit_info[num] -= 1
                    out = stmt()
                else:
                    out = dummy()
                return out
        else:
            @self.callout
            def fn():
                if cond():
                    out = stmt()
                else:
                    out = dummy()
                return out

        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[3], 'NT'), (p.slice[6], 'NT')))

    def p_ifelse(self, p):
        '''ifelse : IFELSE C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE ELSE E_LBRACE stmt E_RBRACE
        '''
        cond, stmt1, stmt2 = p[3], p[6], p[10]

        hit_info = self.hit_info
        if hit_info is not None:
            num1, num2 = get_hash(), get_hash()
            hit_info[num1] += 1
            hit_info[num2] += 1

            @self.callout
            def fn():
                if cond():
                    hit_info[num1] -= 1
                    out = stmt1()
                else:
                    hit_info[num2] -= 1
                    out = stmt2()
                return out
        else:
            @self.callout
            def fn():
                if cond():
                    out = stmt1()
                else:
                    out = stmt2()
                return out

        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[3], 'NT'),
                             (p.slice[6], 'NT'), (p.slice[10], 'NT')))

    def p_while(self, p):
        '''while : WHILE C_LBRACE cond C_RBRACE W_LBRACE stmt W_RBRACE
        '''
        cond, stmt = p[3], p[6]

        hit_info = self.hit_info
        if hit_info is not None:
            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                while(cond()):
                    hit_info[num] -= 1
                    stmt()
        else:
            @self.callout
            def fn():
                while(cond()):
                    stmt()
        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[3], 'NT'), (p.slice[6], 'NT')))

    def p_repeat(self, p):
        '''repeat : REPEAT cste R_LBRACE stmt R_RBRACE
        '''
        cste, stmt = p[2], p[4]

        hit_info = self.hit_info
        if hit_info is not None:
            num = get_hash()
            hit_info[num] += 1

            @self.callout
            def fn():
                for _ in range(cste()):
                    hit_info[num] -= 1
                    stmt()
        else:
            @self.callout
            def fn():
                for _ in range(cste()):
                    stmt()
        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[2], 'NT'), (p.slice[4], 'NT')))

    def p_cond(self, p):
        '''cond : cond_without_not
                | NOT C_LBRACE cond_without_not C_RBRACE
        '''
        if callable(p[1]):
            cond_without_not = p[1]
            fn = lambda: cond_without_not()
            p[0] = fn
            self.actions.append((p.slice[0], (p.slice[1], 'NT')))
        else: # NOT
            cond_without_not = p[3]
            fn = lambda: not cond_without_not()
            p[0] = fn
            self.actions.append((p.slice[0], ('NOT', 'T'), (p.slice[3], 'NT')))


    def p_cond_without_not(self, p):
        '''cond_without_not : FRONT_IS_CLEAR
                            | LEFT_IS_CLEAR
                            | RIGHT_IS_CLEAR
                            | MARKERS_PRESENT
                            | NO_MARKERS_PRESENT
        '''
        cond_without_not = p[1]
        karel = self.karel
        def fn():
            return getattr(karel, cond_without_not)()

        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[1].type, 'T')))

    def p_action(self, p):
        '''action : MOVE
                  | TURN_RIGHT
                  | TURN_LEFT
                  | PICK_MARKER
                  | PUT_MARKER
        '''
        action = p[1]
        karel = self.karel
        def fn():
            return getattr(karel, action)()
        p[0] = fn
        self.actions.append((p.slice[0], (p.slice[1].type, 'T')))

    def p_cste(self, p):
        '''cste : INT
        '''
        value = p[1]
        p[0] = lambda: int(value)
        self.actions.append((p.slice[0], (p.slice[1].value, 'T')))

    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")

cond_map = {
        'FRONT_IS_CLEAR': 'frontIsClear',
        'LEFT_IS_CLEAR': 'leftIsClear',
        'RIGHT_IS_CLEAR': 'rightIsClear',
        'MARKERS_PRESENT': 'markersPresent',
        'NO_MARKERS_PRESENT': 'noMarkersPresent'
    }

action_map = {
        'MOVE': 'move',
        'TURN_RIGHT': 'turnRight',
        'TURN_LEFT': 'turnLeft',
        'PICK_MARKER': 'pickMarker',
        'PUT_MARKER': 'putMarker'
    }


def get_code_from_tree(ast, pretty=False):
    code = get_code_from_ast(ast, beautify=pretty)
    if pretty:
        return beautify(code)
    else:
        return code

# from .parser_base import AST
def get_code_from_ast(ast, beautify=False):
    assert isinstance(ast, AST)
    code = ''
    curr = ast
    if curr.type == 'prog':
        # prog : DEF RUN M_LBRACE stmt M_RBRACE
        code = 'DEF run m( ' + get_code_from_ast(curr.children[0], beautify) + ' m)'
        if beautify:
            code = 'def run () m( ' + get_code_from_ast(curr.children[0] , beautify) + ' m)'
        pass
    elif curr.type == 'stmt':
        # stmt: while | repeat | stmt_stmt | action | if | ifelse
        code = get_code_from_ast(curr.children[0], beautify)
        pass
    elif curr.type == 'stmt_stmt':
        code = get_code_from_ast(curr.children[0], beautify) +\
               ' ' + get_code_from_ast(curr.children[1], beautify)
        if beautify:
            code = get_code_from_ast(curr.children[0] , beautify) + \
                   '\n' + get_code_from_ast(curr.children[1] , beautify) + '\n'
        pass
    elif curr.type == 'if':
        # IF C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE
        code = 'IF c( ' + get_code_from_ast(curr.children[0], beautify) + ' c) i( ' \
                   + get_code_from_ast(curr.children[1], beautify) + ' i)'
        if beautify:
            code = 'if c( ' + get_code_from_ast(curr.children[0] , beautify) + ' c) i( ' \
               + get_code_from_ast(curr.children[1] , beautify) + ' i)'
        pass
    elif curr.type == 'ifelse':
        # ifelse : IFELSE C_LBRACE cond C_RBRACE I_LBRACE stmt I_RBRACE ELSE E_LBRACE stmt E_RBRACE
        code = 'IFELSE c( ' + get_code_from_ast(curr.children[0], beautify) + ' c) i( ' \
                   + get_code_from_ast(curr.children[1], beautify) + \
               ' i) ELSE e( ' + get_code_from_ast(curr.children[2], beautify) \
                    + ' e)'
        if beautify:
            code = 'if c( ' + get_code_from_ast(curr.children[0] , beautify) + ' c) i( ' \
                   + get_code_from_ast(curr.children[1] , beautify) + \
                   ' i) else e( ' + get_code_from_ast(curr.children[2] , beautify) \
                   + ' e)'
        pass
    elif curr.type == 'while':
        # while : WHILE C_LBRACE cond C_RBRACE W_LBRACE stmt W_RBRACE
        code = 'WHILE c( ' + get_code_from_ast(curr.children[0], beautify) + ' c) w( ' \
               + get_code_from_ast(curr.children[1], beautify) + ' w)'
        if beautify:
            code = 'while c( ' + get_code_from_ast(curr.children[0] , beautify) + ' c) w( ' \
                   + get_code_from_ast(curr.children[1] , beautify) + ' w)'
        pass
    elif curr.type == 'repeat':
        # repeat : REPEAT cste R_LBRACE stmt R_RBRACE
        code = 'REPEAT ' + get_code_from_ast(curr.children[0], beautify) + \
               ' r( ' + get_code_from_ast(curr.children[1], beautify) + ' r)'
        if beautify:
            code = 'repeat( ' + get_code_from_ast(curr.children[0] , beautify) + \
                   ') r( ' + get_code_from_ast(curr.children[1] , beautify) + ' r)'
        pass
    elif curr.type == 'cond':
        # cond : cond_without_not | NOT C_LBRACE cond_without_not C_RBRACE
        if len(curr.children) == 1:
            code = get_code_from_ast(curr.children[0], beautify)
        else:
            code = 'not c( ' + get_code_from_ast(curr.children[1], beautify) + ' c)'
            if beautify:
                code = '! c( ' + get_code_from_ast(curr.children[1] , beautify) + ' c)'
        pass
    elif curr.type == 'action':
        # action : MOVE | TURN_RIGHT | TURN_LEFT | PICK_MARKER | PUT_MARKER
        code = action_map[curr.children[0].type] #+ '();'
        if beautify:
            code = code + '();'
        pass
    elif curr.type == 'cond_without_not':
        # cond_without_not : FRONT_IS_CLEAR | LEFT_IS_CLEAR | RIGHT_IS_CLEAR | MARKERS_PRESENT | NO_MARKERS_PRESENT
        code = cond_map[curr.children[0].type] #+ '()'
        if beautify:
            code = code + '()'
        pass
    else:
        # cste : INT
        code = 'R=' + curr.children[0].type
        if beautify:
            code = curr.children[0].type
        pass
    return code





if __name__ == '__main__':
    parser = KarelForSynthesisParser()
    parser_prompt(parser)
