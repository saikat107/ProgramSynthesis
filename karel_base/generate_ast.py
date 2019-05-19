from karel_base.synthesis_parser_only import KarelForSynthesisParserOnly
from karel_base.parser_for_synthesis import get_code_from_tree
import numpy as np
from karel_base.utils import TimeoutError, get_rng, beautify


def g_ast(code):
    try:
        parser = KarelForSynthesisParserOnly()
        parser.debug = False
        parser.new_game(world_size=(8, 8))
        # input = parser.get_state()
        # # print(input.shape)
        parser.init_new_rule_queue()
        parser.run(code, debug=False)
        tree = parser.get_tree()
        # gen_code = get_code_from_tree(tree)
        #
        # parser.init_new_rule_queue()
        # parser.run(gen_code, debug=False)
        # tree2 = parser.get_tree()
        # print(tree)
        # print(tree2)
        # print(code)
        # print(beautify(gen_code))
        #
        # if code != gen_code:
        #     print('-----------------------------------------')
        #     print(tree)
        #     print(tree2)
        #     print(code)
        #     print(gen_code)
        #     print('-----------------------------------------')
        return tree
    except TimeoutError:
        print('Timeout error!\n===============================')
        # g_ast(code)
        print(code)
        print('==============')


# data = np.load('data/test.npz')
# for code in data['codes']:
#     print(code)
#     tree = g_ast(code)
#     print(tree)
#     g_code = get_code_from_tree(tree, pretty=True)
#     # print(g_code)
#     # print('=============================================')

