# Testing Functions
import multiprocessing
import os
import asyncio
from macroflask.util.concurrency_strategy import ConcurrencyContext, ProcessPoolStrategy, \
    ThreadPoolStrategy, CoroutineStrategy
from macroflask.util.simple_log_manager import LogManager

"""
多线程测试，线程池测试
"""


def thread_logging(log_manager):
    """Log messages from multiple threads."""
    app_logger = log_manager.get_logger("app_log")

    for i in range(5):
        app_logger.info(f"Thread logging: Info message {i}")
        app_logger.error(f"Thread logging: Error message {i - 100}")


def check_thread_logging():
    # Multi-Threading Test
    log_manager = LogManager(log_config)
    tasks_with_args = [(thread_logging, (log_manager,)) for index in range(100)]

    context = ConcurrencyContext(ThreadPoolStrategy())
    results = context.execute_tasks(
        tasks_with_args, worker_count=10, logger=log_manager.get_logger("app_log"))
    print(results)


"""
多进程和进程池测试
"""


def process_logging(internal_logger, index):
    """Log messages from multiple processes."""
    print(id(internal_logger))
    for i in range(500):
        internal_logger.bind(app_log=True).info(f"Process logging: Info message {index}")
    internal_logger.complete()

    # app_info_logger = log_manager.get_logger("app_log", "info")
    # app_error_logger = log_manager.get_logger("app_log", "error")
    #
    # for i in range(5):
    #     # if index == 0:
    #     #     time.sleep(3)
    #     app_info_logger.info(f"Process logging: Info message {index + i}")
    #     app_error_logger.error(f"Process logging: Error message {index + i - 100}")


class MockMultiProcessWorker:

    _logger = None

    """
    logru:
        https://loguru.readthedocs.io/en/stable/resources/recipes.html#compatibility-with-multiprocessing-using-enqueue-argument
    """

    @staticmethod
    def set_logger(logger):
        MockMultiProcessWorker._logger = logger

    def work(self, x):
        pid = os.getpid()
        print("current logger id: ", id(self._logger))
        self._logger.bind(app_log=True).info(f"Processing {pid}: {x}")
        self._logger.bind(app_log=True).error(f"Processing {pid}: {x}")
        self._logger.complete()
        return x * x


def check_process_logging():
    # Normal Multi-Processing Test
    # log_manager = LogManager(log_config, enqueue=True).get_raw_logger()
    # processes = []
    # for index in range(8):  # Create 8 processes
    #     process = multiprocessing.Process(target=process_logging, args=(log_manager, index))
    #     processes.append(process)
    #     process.start()
    #
    # for process in processes:
    #     process.join()  # Wait for all processes to finish

    # ProcessPool
    log_manger = LogManager(log_config, enqueue=True).get_raw_logger()
    worker_a = MockMultiProcessWorker()
    tasks_with_args = [(worker_a.work, (index,)) for index in range(100)]

    context = ConcurrencyContext(ProcessPoolStrategy())
    results = context.execute_tasks(
        tasks_with_args, worker_count=10, logger=log_manger.bind(app_log=True),  # for external logger
        initializer=worker_a.set_logger, initargs=(log_manger,)) # for internal logger in process internal
    print(results)


"""
协程测试：
"""


async def work_async(x, new_logger):
    pid = os.getpid()
    if x == 0:
        await asyncio.sleep(3)
    new_logger.bind(app_log=True).info(f"Processing {pid}: {x}")
    new_logger.bind(app_log=True).error(f"Processing {pid}: {x}")
    new_logger.complete()
    return x * x


def check_async_logging():
    """Log messages asynchronously."""
    log_manager = LogManager(log_config, enqueue=True).get_raw_logger()

    tasks_with_args = [(work_async, (index, log_manager, )) for index in range(100)]
    context = ConcurrencyContext(CoroutineStrategy())
    results = context.execute_tasks(
        tasks_with_args, logger=log_manager.bind(app_log=True)) # for internal logger in process internal
    print(results)


log_config = {
    "app_log": {
        "info": {
            "filename": "app_info.log",
            "format": "{time} {level} {message}",
            "rotate": "2s"
        },
        "error": {
            "filename": "app_error.log",
            "format": "{time} {level} {message}",
            "rotate": "2s"
        }
    },
    "sys_log": {
        "info": {
            "filename": "sys_info.log",
            "format": "{time} {level} {message}",
            "rotate": "10 MB"
        },
        "error": {
            "filename": "sys_error.log",
            "format": "{time} {level} {message}",
            "rotate": "10 MB"
        }
    }
}


if __name__ == "__main__":
    # check_thread_logging()

    # check_process_logging()

    check_async_logging()