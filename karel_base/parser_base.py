from __future__ import print_function

import random
import ply.lex as lex
from functools import wraps
from collections import defaultdict as defaultdic
import karel_base.yacc as yacc
from karel_base.karel import Karel
from karel_base.utils import pprint, timeout, get_rng, str2bool, TimeoutError


class Hypothesis:
    def __init__(self):
        # assert isinstance(root, ASTNode)
        self.tree = AST('prog', 'NT')
        self.frontier_stack = [self.tree]
        self.t = 0



    def copy_tree(self, arg, root):
        assert isinstance(arg, Hypothesis)
        assert isinstance(root, AST)
        root_node = AST(root.type, root.value)
        if root in arg.frontier_stack:
            idx = arg.frontier_stack.index(root)
            self.frontier_stack[idx] = root_node
        new_children = []
        for child in root.children:
            new_child = self.copy_tree(arg, child)
            new_child.parent = root
            new_children.append(new_child)
        root_node.children = new_children
        return root_node

    def is_completed(self):
        return len(self.frontier_stack) == 0

    def frontier_node(self):
        if not self.is_completed():
            return self.frontier_stack[-1]
        else:
            return None

    def apply_rule(self, rule, rule_probability=1.0):
        # assert isinstance(rule, Rule)
        parent = rule[0]
        # assert isinstance(parent, ASTNode)

        children = rule[1]
        # print(children)
        fnt = self.frontier_stack.pop()# This is the frontier node, this node should be expanded

        # fnt.applied_rule = rule
        if fnt.type == parent:
            num_child = len(children)
            new_children = []
            for i in range(num_child):
                new_child = AST(children[i][0], children[i][1])
                # print(new_child.value)
                new_child.parent = fnt
                new_children.append(new_child)
            fnt.children = new_children
            for i in range(num_child):
                child = new_children[i]
                if child.value.strip() == 'NT':
                    # print(child.type, child.value)
                    self.frontier_stack.append(child)

            # fnt = self.frontier_stack.pop()
            # while self.grammar.is_value_node(fnt):
            #     self.frontier_stack.pop()
            # self.frontier_stack.append(fnt)
        else :
            print(fnt.type, parent)
            raise ValueError('Invalid Rule, Rule Head does not match with the frontier node!')
        # if config.per_action_score:
        #     self.score = ((self.score * self.t) + np.log2(rule_probability)) / (self.t + 1)
        # else:
        #     self.score = self.score + np.log2(rule_probability)


    def __repr__(self):
        try:
            frontier = self.frontier_node()
        except:
            frontier = 'Already Completed'
        # return 'Tree : ' + str(self.tree) + '\n' + 'Stack : ' + str(self.frontier_stack) + \
        #        '\nFrontier : ' + str(frontier) + '\n\n'
        return str(self.tree)

    def get_action_parent_t(self):
        try:
            frontier = self.frontier_node()
        except:
            frontier = None
        if frontier is not None:
            if frontier.parent is None:
                return -1
            else:
                return frontier.parent.t
        else:
            return 0

    def stack_equal(self, other):
        assert isinstance(other, Hypothesis)
        if len(self.frontier_stack) == len(other.frontier_stack):
            for a, b in zip(self.frontier_stack, other.frontier_stack):
                assert isinstance(a, AST) and isinstance(b, AST)
                if a.type != b.type or a.label != b.label or a.value != b.value:
                    return False
            return True
        else:
            return False

    def tree_equal(self, other):
        return self.tree.tree_equal(other.tree)

    def __eq__(self, other):
        return self.stack_equal(other) and self.tree_equal(other)

    def __hash__(self):
        return str(self.tree).__hash__()

    def get_terminal_sequence(self):
        if self.tree is None:
            return None
        return self.tree.get_leaf_typ_sequence()
        pass


class Parser(object):
    """
    Base class for a lexer/parser that has the rules defined as methods.
    """
    tokens = ()
    precedence = ()

    def __init__(self, rng=None, min_int=0, max_int=19,
                 max_func_call=500, debug=False, **kwargs):

        self.names = {}
        self.debug = False#kwargs.get('debug', 0)

        # Build the lexer and parser
        modname = self.__class__.__name__

        self.lexer = lex.lex(module=self, debug=self.debug)

        self.yacc, self.grammar = yacc.yacc(
                module=self,
                debug=self.debug,
                tabmodule="_parsetab",
                with_grammar=True)

        self.prodnames = self.grammar.Prodnames

        #########
        # main
        #########

        self.debug = True#debug
        self.min_int = min_int
        self.max_int = max_int
        self.max_func_call = max_func_call
        self.int_range = list(range(min_int, max_int+1))

        int_tokens = ['INT{}'.format(num) for num in self.int_range]
        self.tokens_details = list(set(self.tokens) - set(['INT'])) + int_tokens

        #self.idx_to_token = { idx: token for idx, token in enumerate(tokens) }
        #self.token_to_idx = { token:idx for idx, token in idx_to_token.items() }

        self.tokens_details.sort()
        self.tokens_details = ['END'] + self.tokens_details

        self.idx_to_token_details = {
                idx: token for idx, token in enumerate(self.tokens_details) }
        self.token_to_idx_details = {
                token:idx for idx, token in self.idx_to_token_details.items() }

        self.rng = get_rng(rng)
        self.flush_hit_info()
        self.call_counter = [0]

        def callout(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                if self.call_counter[0] > self.max_func_call:
                    raise TimeoutError
                r = f(*args, **kwargs)
                self.call_counter[0] += 1
                return r
            return wrapped

        self.callout = callout
        self.init_new_rule_queue()

    def lex_to_idx(self, code, details=False):
        tokens = []
        self.lexer.input(code)
        while True:
            tok = self.lexer.token()
            if not tok:
                break

            if details:
                if tok.type == 'INT':
                    idx = self.token_to_idx_details["INT{}".format(tok.value)]
                else:
                    idx = self.token_to_idx_details[tok.type]
            else:
                idx = self.token_to_idx[tok.type]
            tokens.append(idx)
        # print(tokens)
        return tokens


    #########
    # Karel
    #########

    def get_state(self):
        return self.karel.state

    def run(self, code, with_timeout=False, **kwargs):
        code_hash = hash(code)
        self.call_counter = [0]

        if code_hash in self.funct_table:
            def fn():
                return self.funct_table[code_hash]()
        else:
            yacc = self.yacc
            def fn():
                cd = yacc.parse(code, **kwargs)()
                return cd
            self.funct_table[code_hash] = fn

        out = fn()
        return out

    def new_game(self, **kwargs):
        self.karel = Karel(rng=self.rng, **kwargs)
        self.init_new_rule_queue()

    def draw(self, *args, **kwargs):
        return self.karel.draw(*args, **kwargs)

    def draw_for_tensorboard(self):
        return "\t" + "\n\t".join(self.draw(no_print=True))

    def random_code(self, create_hit_info=False, *args, **kwargs):
        code = " ".join(self.random_tokens(*args, **kwargs))

        # check minimum # of move()
        min_move = getattr(kwargs, 'min_move', 0)
        count_diff = min_move - code.count(self.t_MOVE)

        if count_diff > 0:
            action_candidates = []
            tokens = code.split()

            for idx, token in enumerate(tokens):
                if token in self.action_functions and token != self.t_MOVE:
                    action_candidates.append(idx)

            idxes = self.rng.choice(
                    action_candidates, min(len(action_candidates), count_diff))
            for idx in idxes:
                tokens[idx] = self.t_MOVE
            code = " ".join(tokens)

        if create_hit_info:
            self.hit_info = defaultdict(int)
        else:
            self.hit_info = None

        return code

    def random_tokens(self, start_token="prog", depth=0, stmt_min_depth=2, stmt_max_depth=5, **kwargs):
        #print(depth, start_token)
        if start_token == 'stmt':
            if depth > stmt_max_depth:
                start_token = "action"
            #if depth < 2:
            #    start_token = self.rng.choice(
            #            ['action'] * 1
            #            + ['while'] * 4
            #            + ['repeat'] * 4
            #            + ['stmt_stmt'] * 16
            #            + ['if', 'ifelse'] * 4, 1)[0]

        codes = []
        candidates = self.prodnames[start_token]

        prod = candidates[self.rng.randint(len(candidates))]

        for term in prod.prod:
            if term in self.prodnames: # need digging
                codes.extend(self.random_tokens(term, depth + 1, stmt_max_depth))
            else:
                token = getattr(self, 't_{}'.format(term))
                if callable(token):
                    if token == self.t_INT:
                        token = self.random_INT()
                    else:
                        raise Exception(" [!] Undefined token `{}`".format(token))

                codes.append(str(token).replace('\\', ''))

        return codes

    def flush_hit_info(self):
        self.hit_info = None
        self.funct_table = {} # save parsed function

    def init_new_rule_queue(self):
        self.actions = []

    def get_action_sequence(self):
        actions = []
        for action in self.actions:
            action = list(action)
            rule_head = str(action[0])
            rule_bodys = action[1:]
            rule_body_list = []
            for rule_body in rule_bodys:
                rule_body_list.append((str(rule_body[0]), str(rule_body[1])))
            actions.append((rule_head, rule_body_list))
        actions.reverse()
        return actions

    def get_tree(self):
        actions = self.get_action_sequence()
        hyp = Hypothesis()
        for action in actions:
            hyp.apply_rule(action)
        tree = hyp.tree
        # print(tree)
        return tree



class AST:
    def __init__(self, t, v, c=[], p=None):
        self.type = t
        self.value = v
        self.children = c
        self.parent = p

    def __repr__(self):
        return treestr(self, 0)


def treestr(node, level):
    s = ''
    for i in range(level):
        s += '    '
    s += str(node.type) + ' ' + str(node.value) + '\n'
    for child in node.children:
        s += treestr(child, level + 1)
    return s

def dummy():
    pass

def get_hash():
    return random.getrandbits(128)

def parser_prompt(parser):
    import argparse
    #from prompt_toolkit import prompt
    #from prompt_toolkit.token import Token

    #def continuation_tokens(cli, width):
    #    return [(Token, ' ' * (width - 5) + '.' * 3 + ':')]

    def is_multi_line(line):
        return line.strip()

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--debug', type=str2bool, default=False)
    arg_parser.add_argument('--world', type=str, default=None, help='Path to world text file')
    arg_parser.add_argument('--world_height', type=int, default=8, help='Height of square grid world')
    arg_parser.add_argument('--world_width', type=int, default=8, help='Width of square grid world')
    args = arg_parser.parse_args()

    line_no = 1
    parser.debug = args.debug

    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    while True:
        code = 'DEF run m( REPEAT R=5 r( move r) m)'# input()#prompt(u'In [{}]: '.format(line_no), multiline=True,
                      #get_continuation_tokens=continuation_tokens)

        if args.world is not None:
            parser.new_game(world_path=args.world)
        else:
            parser.new_game(world_size=(args.world_width, args.world_height))

        parser.init_new_rule_queue()
        parser.draw("Input:  ", with_color=True)
        parser.run(code, debug=False)
        parser.draw("Output: ", with_color=True)
        parser.get_tree()
        line_no += 1
        exit()
