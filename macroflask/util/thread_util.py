import concurrent.futures


class ThreadMethodFactory:

    @classmethod
    def exec_in_thread_pool(cls, loop_obj_list, func_list, thread_num: int, **kwargs):
        """
        Execute the function in the thread pool.

        :param loop_obj_list:  list of objects to loop
        :param func_list:      function list to execute,
            the length of the function list should be the same as the loop object list
        :param thread_num:     number of threads
        :param kwargs:         additional keyword arguments

        :return:               list of task results

        :exception             ValueError: The length of the loop object list and the function list should be the same.
        """

        if len(loop_obj_list) != len(func_list):
            raise ValueError("The length of the loop object list and the function list should be the same.")

        with concurrent.futures.ThreadPoolExecutor(max_workers=thread_num) as executor:
            futures = []
            task_result_list = []
            for index, obj in enumerate(loop_obj_list):
                func_name = func_list[index]
                future = executor.submit(func_name, obj, **kwargs)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    task_result_list.append(result)
                except Exception as e:
                    task_result_list.append((False, str(e)))

        return task_result_list


if __name__ == '__main__':
    def func1(obj, **kwargs):
        return f"func1: {obj} with {kwargs}"


    def func2(obj, **kwargs):
        return f"func2: {obj} with {kwargs}"


    result = ThreadMethodFactory.exec_in_thread_pool(
        loop_obj_list=[1, 22, 111 ,2111],
        func_list=[func1, func2, func1, func2],
        thread_num=2,
        additional_arg="test"
    )

    for res in result:
        print(res)
