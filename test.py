import numpy as np
from karel_base import karel
from karel_base.parser_for_synthesis import KarelForSynthesisParser
from karel_base.utils import beautify, TimeoutError
import pickle
import os


if not os.path.exists('processed_data'):
    os.mkdir('processed_data')
for datatype in ['test', 'train', 'val']:
    data = np.load('data/' + datatype + '.npz')
    print('Read : ' + datatype + '.npz')
    full_data = []
    # codes = ['DEF run m( IFELSE c( frontIsClear c) i( turnRight move i) ELSE e( turnLeft move e) IFELSE c( leftIsClear c) i( turnRight move i) ELSE e( turnLeft move e) m)']
    print('# examples : ', len(data['codes']))
    for idx, code in enumerate(data['codes']):
        if idx % 100 == 0:
            print(idx)
        parser = KarelForSynthesisParser()
        inputs = []
        outputs = []
        valid_inputs = []
        traces = []
        vectors = []
        count= 0
        total = 0
        success = True
        # print(beautify(code))
        examples = []
        counter_ex = 0
        while count != 6:
            try:
                total = 0
                parser.new_game(world_size=(8, 8))
                parser.karel.init_execution_trace()
                input_state = parser.get_state()
                # assert isinstance(input_state, np.ndarray)
                if input_state.tobytes() in valid_inputs:
                    raise IndexError('repeat')
                parser.run(code)
                output_state = parser.get_state()
                execution_trace = parser.karel.get_execution_trace()
                if len(execution_trace) == 0:
                    counter_ex += 1
                    raise IndexError('no_exec')
                trace_vectors = parser.karel.get_condition_trace()
                vectors.append(trace_vectors)
                count += 1
                inputs.append(input_state)
                outputs.append(output_state)
                traces.append(execution_trace)
                example_details = {
                    'input': input_state,
                    'output': output_state,
                    'trace': execution_trace,
                    'state_vectors': trace_vectors
                }
                examples.append(example_details)
                valid_inputs.append(input_state.tobytes())
            except IndexError as e:
                # print(e)
                # print(total, counter_ex)
                total += 1
                if total == 25:
                    success = False
                    break
                if counter_ex == 25:
                    success = False
                    break
            except TimeoutError as e:
                # print(e)
                # print(total, counter_ex)
                total += 1
                if total == 25:
                    success = False
                    break
                if counter_ex == 25:
                    success = False
                    break
        if success:
            data_dict = {
                'code': code,
                'examples': examples
            }
            full_data.append(data_dict)
            # print(data_dict)
    dest_file = 'processed_data/' + datatype +  '.npz'
    np.savez(dest_file, data=full_data)
    # dest_file.close()

