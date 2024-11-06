import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed


class ConcurrencyStrategy:
    def execute(self, tasks_with_args, worker_count, **kwargs):
        """Execute tasks concurrently, each task can receive different arguments, and support worker configuration"""
        raise NotImplementedError("Strategy must implement execute method.")


class ThreadPoolStrategy(ConcurrencyStrategy):
    def execute(self, tasks_with_args, worker_count, logger=None, **kwargs):
        if logger:
            logger.info(f"Using threads to execute tasks, worker count: {worker_count}...")
        else:
            print(f"Using threads to execute tasks, worker count: {worker_count}...")

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = []  # Store all task Future objects
            for task, args in tasks_with_args:
                try:
                    future = executor.submit(lambda: task(*args))  # Submit task
                    futures.append(future)
                except Exception as e:
                    error_msg = f"Task submission failed: {e}"
                    if logger:
                        logger.error(error_msg)
                    else:
                        print(error_msg)

            # Collect results as they complete
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()  # Get task result
                    results.append((True, result))  # Success status and result
                except Exception as e:
                    error_msg = f"Task execution failed: {e}"
                    if logger:
                        logger.error(error_msg)
                    else:
                        print(error_msg)
                    results.append((False, error_msg))  # Failure status and error message

        return results


class ProcessPoolStrategy(ConcurrencyStrategy):
    def execute(self, tasks_with_args, worker_count, logger=None, **kwargs):
        if logger:
            logger.info(f"Using processes to execute tasks, worker count: {worker_count}...")

        with ProcessPoolExecutor(max_workers=worker_count, **kwargs) as executor:
            futures = []  # Store all task Future objects
            for task, args in tasks_with_args:
                try:
                    future = executor.submit(task, *args)  # Submit task
                    futures.append(future)
                except Exception as e:
                    error_msg = f"Task submission failed: {e}"
                    if logger:
                        logger.error(error_msg)
                    else:
                        print(error_msg)
                    futures.append((False, error_msg))  # Store failure status for submission error

            # Collect results as they complete
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()  # Get task result
                    results.append((True, result))  # Success status and result
                except Exception as e:
                    error_msg = f"Task execution failed: {e}"
                    if logger:
                        logger.error(error_msg)
                    else:
                        print(error_msg)
                    results.append((False, error_msg))  # Failure status and error message

        return results


class CoroutineStrategy(ConcurrencyStrategy):
    async def async_execute(self, tasks_with_args, worker_count=None, logger=None):
        if logger:
            logger.info("Executing tasks using coroutines with limited worker count...")

        # Set up a semaphore to limit the concurrency level
        semaphore = asyncio.Semaphore(worker_count) if worker_count else None

        async def run_task(task, args):
            try:
                # Wait for a slot if worker count is limited
                if semaphore:
                    async with semaphore:
                        result = await task(*args)  # Run the coroutine task with args
                else:
                    result = await task(*args)
                return (True, result)
            except Exception as e:
                error_msg = f"Task execution failed: {e}"
                if logger:
                    logger.error(error_msg)
                else:
                    print(error_msg)
                return (False, error_msg)

        # Create coroutine tasks for all input tasks
        tasks = [run_task(task, args) for task, args in tasks_with_args]

        # Execute all tasks concurrently with control on worker count
        return await asyncio.gather(*tasks)

    def execute(self, tasks_with_args, worker_count=None, logger=None):
        return asyncio.run(self.async_execute(tasks_with_args, worker_count, logger))


class ConcurrencyContext:
    def __init__(self, strategy: ConcurrencyStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: ConcurrencyStrategy):
        self._strategy = strategy

    def execute_tasks(self, tasks_with_args, worker_count=None, **kwargs):
        return self._strategy.execute(tasks_with_args, worker_count, **kwargs)


if __name__ == '__main__':
    # 示例任务函数，接受不同数量的参数
    # Example coroutines (to simulate real tasks)
    async def task1(arg1, arg2):
        await asyncio.sleep(10)  # Simulate async work
        print("task1: " + str(1))
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
        (task1, (2, 3)),  # task_1 接收 2 个参数
        (task2, (4, 5, 6)),  # task_2 接收 3 个参数，并且会抛出异常
        (task3, (7,))  # task_3 接收 1 个参数
    ]

    # 初始化上下文并选择策略
    context = ConcurrencyContext(ThreadPoolStrategy())  # 使用多线程
    # results = context.execute_tasks(tasks_with_args, worker_count=3)
    # print(results)

    # 切换到多进程策略
    # context.set_strategy(ProcessPoolStrategy())  # 使用多进程
    # results = context.execute_tasks(tasks_with_args, worker_count=3)
    # print(results)

    # 切换到协程策略
    context.set_strategy(CoroutineStrategy())  # 使用协程
    results = context.execute_tasks(tasks_with_args)
    print(results)