import asyncio
import time

from macroflask.util.concurrency_strategy import ConcurrencyContext, CoroutineStrategy, \
    ThreadPoolStrategy, ProcessPoolStrategy


def check_coroutine_strategy():
    async def task1(arg1, arg2):
        await asyncio.sleep(10)  # Simulate async work
        print("task1: The task is the last task to be executed")
        raise Exception("任务1抛出异常")
        return arg1 + arg2

    async def task2(arg1, arg2, arg3):
        await asyncio.sleep(2)  # Simulate async work
        print("task2: " + str(2))
        return arg1 * arg2 * arg3

    async def task3(arg1):
        await asyncio.sleep(1)  # Simulate async work
        print("task3: " + str(3))
        return arg1 ** 2

    # 创建任务和对应参数的列表
    tasks_with_args = [
        (task1, (2, 3)),
        (task2, (4, 5, 6)),
        (task3, (7,))
    ]

    # 初始化上下文并选择策略
    context = ConcurrencyContext(CoroutineStrategy())
    results = context.execute_tasks(tasks_with_args, worker_count=3)
    print(results)


def check_thread_strategy():
    def task1(arg1, arg2):
        time.sleep(10)  # Simulate async work
        print("task1: The task is the last task to be executed")
        raise Exception("任务1抛出异常")
        return arg1 + arg2

    def task2(arg1, arg2, arg3):
        time.sleep(2)  # Simulate async work
        print("task2: " + str(2))
        return arg1 * arg2 * arg3

    def task3(arg1):
        time.sleep(1)  # Simulate async work
        print("task3: " + str(3))
        return arg1 ** 2

    tasks_with_args = [
        (task1, (2, 3)),
        (task2, (4, 5, 6)),
        (task3, (7,))
    ]

    # 切换到多线程策略
    context = ConcurrencyContext(CoroutineStrategy())
    context.set_strategy(ThreadPoolStrategy())  # 使用多进程
    results = context.execute_tasks(tasks_with_args, worker_count=3)
    print(results)


def process_task1(arg1, arg2):
    time.sleep(10)  # Simulate async work
    print("task1: The task is the last task to be executed")
    raise Exception("任务1抛出异常")
    return arg1 + arg2


def process_task2(arg1, arg2, arg3):
    time.sleep(2)  # Simulate async work
    print("task2: " + str(2))
    return arg1 * arg2 * arg3


def process_task3(arg1):
    time.sleep(1)  # Simulate async work
    print("task3: " + str(3))
    return arg1 ** 2


def check_process_strategy():
    tasks_with_args = [
        (process_task1, (2, 3)),
        (process_task2, (4, 5, 6)),
        (process_task3, (7,))
    ]

    # 切换到多线程策略
    context = ConcurrencyContext(ProcessPoolStrategy())
    results = context.execute_tasks(tasks_with_args, worker_count=3)
    print(results)


if __name__ == '__main__':

    # # 测试协程策略
    check_coroutine_strategy()
    #
    # # 测试多线程策略
    # check_thread_strategy()

    # 测试多进程策略
    # check_process_strategy()