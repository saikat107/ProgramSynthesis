import numpy as np
from karel_base import karel
from karel_base.parser_for_synthesis import KarelForSynthesisParser
from karel_base.utils import beautify
import pickle

data = np.load('data/test.npz')
full_data = []
for code in data['codes']:
    parser = KarelForSynthesisParser()
    inputs = []
    outputs = []
    valid_inputs = []
    traces = []
    count= 0
    total = 0
    success = True
    # print(beautify(code))
    while count != 6:
        try:
            total = 0
            parser.new_game(world_size=(8, 8))
            parser.karel.init_execution_trace()
            input_state = parser.get_state()
            # assert isinstance(input_state, np.ndarray)
            if input_state.tobytes() in valid_inputs:
                parser.draw()
                total += 1
                if total == 25:
                    success = False
                    break
                continue
            # else:
            #     parser.draw()
            parser.run(code)
            output_state = parser.get_state()
            execution_trace = parser.karel.get_execution_trace()
            count += 1
            inputs.append(input_state)
            outputs.append(output_state)
            traces.append(execution_trace)
            valid_inputs.append(input_state.tobytes())
        except:
            total += 1
            if total == 25:
                success = False
                break

    if success:
        full_data.append({
            'code': code,
            'inputs': inputs,
            'outputs': outputs,
            'trace': traces
        })
        print(beautify(code))
        print(len(inputs), len(outputs))
        for trace in traces:
            print(trace)
        print('='*50)

dest_file = open('data.bin', 'wb')
pickle.dump(full_data, dest_file)
dest_file.close()

