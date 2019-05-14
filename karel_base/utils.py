import os
import errno
import signal
from datetime import datetime

import numpy as np
from functools import wraps
from pyparsing import nestedExpr


class TimeoutError(Exception):
    pass

def str2bool(v):
    return v.lower() in ('true', '1')

class Tcolors:
    CYAN = '\033[1;30m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def traverse(parseObject):
    name = parseObject.slice[0]
    childs = parseObject.slice



def debug(*msg):
    time = datetime.now()
    timestr = str(time.strftime('%X'))
    import inspect
    file_path = inspect.stack()[1][1]
    line_num = inspect.stack()[1][2]
    file_name = file_path
    if os.getcwd() in file_path:
        file_name = file_path[len(os.getcwd())+1:]
    stack = str(file_name) + '#' + str(line_num) + ' [' + timestr + ']'
    print(stack, end=' ')
    res = '\t'
    for ms in msg:
        res += (str(ms) + ' ')
    print(res)


def timeout(seconds=500, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.setitimer(signal.ITIMER_REAL,seconds) #used timer instead of alarm
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result
        return wraps(func)(wrapper)
    return decorator

def beautify_fn(inputs, indent=1, tabspace=2):
    lines, queue = [], []
    space = tabspace * " "

    for item in inputs:
        if item == ";":
            lines.append(" ".join(queue))
            queue = []
        elif type(item) == str:
            queue.append(item)
        else:
            lines.append(" ".join(queue + ["{"]))
            queue = []

            inner_lines = beautify_fn(item, indent=indent+1, tabspace=tabspace)
            lines.extend([space + line for line in inner_lines[:-1]])
            lines.append(inner_lines[-1])

    if len(queue) > 0:
        lines.append(" ".join(queue))

    return lines + ["}"]

def pprint(code, *args, **kwargs):
    print(beautify(code, *args, **kwargs))

replace_dict = {
        'm(': '{',
        'm)': '}',
        'c(': '(',
        'c)': ')',
        'r(': '{',
        'r)': '}',
        'w(': '{',
        'w)': '}',
        'i(': '{',
        'i)': '}',
        'e(': '{',
        'e)': '}',
}

def beautify(code, tabspace=2):
    code = " ".join(replace_dict.get(token, token) for token in code.split())
    array = nestedExpr('{','}').parseString("{"+code+"}").asList()
    lines = beautify_fn(array[0])
    return "\n".join(lines[:-1]).replace(' ( ', '(').replace(' )', ')')

def makedirs(path):
    if not os.path.exists(path):
        print(" [*] Make directories : {}".format(path))
        os.makedirs(path)

def get_rng(rng, seed=123):
    if rng is None:
        rng = np.random.RandomState(seed)
    return rng
