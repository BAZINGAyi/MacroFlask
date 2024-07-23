import os
import psutil
import tracemalloc


def show_memory_info(hint):
    pid = os.getpid()
    p = psutil.Process(pid)

    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    print('{} memory used: {} MB'.format(hint, memory))
    return memory


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


if __name__ == '__main__':
    MemoryTopUtil.start_trace()
    MemoryTopUtil.mock_create_leak()
    MemoryTopUtil.display_top_10()