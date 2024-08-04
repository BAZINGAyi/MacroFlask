import os
import time
import uuid

import psutil
import tracemalloc


def show_memory_info(hint):
    pid = os.getpid()
    p = psutil.Process(pid)

    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    print('{} memory used: {} MB'.format(hint, memory))
    return memory


def print_run_time(func):
    """
    Print the run time of the function

    :param func: function object
    :return:
    """
    def wrapper(*args, **kw):
        local_time = time.time()
        result = func(*args, **kw)
        print('current Function [%s] run time is %.2f' % (func.__name__, time.time() - local_time))
        return result
    return wrapper


class MemoryTopUtil:

    @staticmethod
    def start_trace():
        tracemalloc.start()

    @staticmethod
    def display_top_10():
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.compare_to(snapshot, 'lineno')

        print("Top 10 lines with the highest memory allocations:")
        for stat in top_stats[:10]:
            print(stat)

    @staticmethod
    def mock_create_leak():
        leaky_objects = []

        class Leaky:
            def __init__(self):
                self.data = [i for i in range(10000)]

        for _ in range(100):
            leaky_objects.append(Leaky())
        return leaky_objects


class UUIDUtil:
    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())


if __name__ == '__main__':
    MemoryTopUtil.start_trace()
    MemoryTopUtil.mock_create_leak()
    MemoryTopUtil.display_top_10()