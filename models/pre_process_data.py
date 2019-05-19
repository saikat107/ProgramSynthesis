import numpy as np
import os
from karel_base.generate_ast import g_ast
from karel_base.parser_base import AST
from karel_base.utils import debug


def traverse_ast(root):
    assert isinstance(root, AST)
    rules = list()
    stack = list()
    stack.append(root)
    while len(stack) != 0:
        curr = stack.pop()
        if curr.value == 'NT':
            children = curr.children
            rule_str = curr.type + '->'
            child_str = [child.type for child in children]
            rule_str += ','.join(child_str)
            rules.append(rule_str)
            for child in children[::-1]:
                stack.append(child)
    return ' '.join(rules)


if __name__ == '__main__':
    input_path = 'processed_data'
    output_path = 'models/data/raw_concat'
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    data_sets = ['test', 'val', 'train']
    for data_name in data_sets:
        final_data_input = open(output_path + '/' + data_name + '.input', 'w')
        final_data_code = open(output_path + '/' + data_name + '.code', 'w')
        final_data_tree = open(output_path + '/' + data_name + '.tree', 'w')

        data_path = input_path + '/' + data_name + '.npz'
        data = np.load(data_path)['data']
        for idx, d_example in enumerate(data):
            if idx % 500 == 0:
                debug(data_name, idx)
            code = d_example['code']
            ast = g_ast(code)
            rule_str = traverse_ast(ast)
            # debug(ast)
            # debug(rule_str)
            input_str_vector = list()
            examples = d_example['examples']
            for example in examples:
                actions = ['null']
                actions.extend(example['trace'])
                states = example['state_vectors']
                input_feature_vector = list()
                for action, vector in zip(actions, states):
                    input_feature_str = list()
                    input_feature_str.append(str(action))
                    input_feature_str.append(str(vector['agent_status']))
                    input_feature_str.extend([str(i) for i in vector['condition_vector']])
                    input_feature_vector.append(u"|".join(input_feature_str))
                    # print(action, vector['agent_status'], *vector['condition_vector'], sep=u'|')
                input_feature_vector.append(u"</s>|^|0|0|0|0|0")
                input_str_vector.append(' '.join(input_feature_vector))
            input_str = u" ".join(input_str_vector)
            # print(input_str)
            final_data_input.write(input_str + '\n')
            final_data_code.write(code + '\n')
            final_data_tree.write(rule_str + '\n')
        final_data_input.close()
        final_data_code.close()
        final_data_tree.close()

