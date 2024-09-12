import os
import sys
import time

from macroflask.util.light_logging import MacroFlaskLogger

# append the root directory of the project to sys.path
current_directory = os.path.dirname(os.path.abspath(__file__))
current_directory = os.path.dirname(current_directory)
current_directory = os.path.dirname(current_directory)
print(current_directory)
sys.path.append(current_directory)


def check_multi_threads():
    from config import Config, get_config
    import threading
    logger_manager = MacroFlaskLogger(Config.LOGGING)

    def write_log(logger_type):
        if logger_type == 0:
            app_logger = logger_manager.get_logger("app")
            app_logger.debug("2")
            app_logger.info("3")
            app_logger.warning("4")
            app_logger.error("5")
            app_logger.critical("6")

        elif logger_type == 1:
            sys_logger = logger_manager.get_logger("sys")
            sys_logger.debug("10")
            sys_logger.info("20")
            sys_logger.warning("30")
            sys_logger.error("40")
            sys_logger.critical("50")

    # start multi-threading to test
    threads = [threading.Thread(target=write_log, args=(index % 2,)) for index in range(100)]
    for thread in threads:
        thread.start()

    # wait for all threads to finish
    for thread in threads:
        thread.join()

    logger_manager.shutdown()


def write_log(logger_type):
    from config import Config
    logger_manager = MacroFlaskLogger(Config.LOGGING)
    if logger_type == 0:
        app_logger = logger_manager.get_logger("app")
        app_logger.debug("2")
        app_logger.info("3")
        app_logger.warning("4")
        app_logger.error("5")
        app_logger.critical("6")

    elif logger_type == 1:
        sys_logger = logger_manager.get_logger("sys")
        sys_logger.debug("10")
        sys_logger.info("20")
        sys_logger.warning("30")
        sys_logger.error("40")
        sys_logger.critical("50")

    logger_manager.shutdown()


if __name__ == '__main__':
    # check_multi_threads()
    # start multi-processing to test
    start_time = int(time.time())
    end_time = start_time + 60
    current_time = start_time
    while current_time <= end_time:
        import multiprocessing
        processes = [multiprocessing.Process(target=write_log, args=(index % 2,)) for index in range(4)]
        for process in processes:
            process.start()

        for process in processes:
            process.join()

        time.sleep(20)
        current_time = int(time.time())
