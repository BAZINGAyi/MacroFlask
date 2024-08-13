import os
import profile
import random
import sys
import tracemalloc

# append the root directory of the project to sys.path
current_directory = os.path.dirname(os.path.abspath(__file__))
current_directory = os.path.dirname(current_directory)
current_directory = os.path.dirname(current_directory)
print(current_directory)
sys.path.append(current_directory)

import threading
import time
from config import get_config
import psutil

from flask import Flask
from macroflask.util.light_sqlalchemy import LightSqlAlchemy
from macroflask.util.os_util import show_memory_info


class TestLightSQLAlchemy:

    def show_memory_info(self, hint):
        pid = os.getpid()
        p = psutil.Process(pid)

        info = p.memory_full_info()
        memory = info.uss / 1024. / 1024
        print('{} memory used: {} MB'.format(hint, memory))

    def test_light_memory_lose_in_non_flask_env(self):
        from macroflask.system.user_model import User, Base

        def worker():
            with lsa.get_db_session() as session:
                # Perform database operations
                # print("session-id" + str(id(session)))
                user = session.query(User).where().first()
                username = user.username
                # users = session.query(User).all()
                # for user in users:
                #     aa = user.username
                #     # print(user.username)
                #     pass

            # with lsa.get_non_flask_session() as session:
            #     # print(id(session))
            #     users = session.query(User).all()
            #     for user in users:
            #         aa = user.username
            #         # print(user.username)
            #         pass

        # Test the LightSQLAlchemy class
        db_config = {
            'database1': {
                'url': get_config().DATABASE_URI,
                "model_class": Base,
                "engine_options": {},
                "session_options": {}
            }
        }
        lsa = LightSqlAlchemy(is_flask=False, db_config=db_config)

        # test rime range
        start_time = int(time.time())
        end_time = start_time + 60 * 5

        # Test the worker function
        memory_statistic = []
        current_time = start_time
        while current_time <= end_time:
            current_time = int(time.time())

            print("exec_sql")
            threads = [threading.Thread(target=worker) for _ in range(50)]
            for thread in threads:
                thread.start()

            # wait for all threads to finish
            for thread in threads:
                thread.join()
            print("end_sql")

            # getrefcount() returns the reference count of the object
            print(sys.getrefcount(lsa))
            print("done")
            time.sleep(30)

            memory_statistic.append(show_memory_info("Current"))

            # Take a snapshot of the current memory usage
            # tracemalloc.start()
            # snapshot = tracemalloc.take_snapshot()
            # top_stats = snapshot.compare_to(snapshot, 'lineno')
            #
            # print("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz")
            # print("Top 10 lines with the highest memory allocations:")
            # for stat in top_stats[:5]:
            #     print(stat)
        print(memory_statistic)

    def check_concurrent_with_one_db(self):
        # Q1 100 并发，没有内存泄露的问题,
        # SELECT * FROM information_schema.PROCESSLIST where ID NOT IN (6472, 8759, 8841);
        # SHOW VARIABLES LIKE 'max_connections';
        # 测试 memory 占用

        from sqlalchemy import Integer, String, Column
        from sqlalchemy.orm import Mapped
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        # none-flask environment
        db_config_dict = {
            'database1': {
                'url': get_config().DATABASE_URI,
                "model_class": Base,
                "engine_options": {
                    # "pool_size": 5,  # 增大连接池大小
                    # "max_overflow": 1,  # 增大溢出连接数
                    # "pool_timeout": 1,  # 增加连接超时时间（秒）
                    # "pool_recycle": 5,  # 重置连接池中的空闲连接的超时时间（秒）
                },
                "session_options": {}
            }
        }
        lsa = LightSqlAlchemy(db_config=db_config_dict)

        def worker():
            with lsa.get_db_session() as session:
                # Perform database operations
                # print("session-id" + str(id(session)))
                # users = session.query(User).all()
                # for user in users:
                #     # print(user.username)
                #     pass
                user = session.query(User).where().first()
                username = user.username

        # test rime range
        start_time = int(time.time())
        end_time = start_time + 60 * 5

        # Test the worker function
        memory_statistic = []
        current_time = start_time
        while current_time <= end_time:
            threads = [threading.Thread(target=worker) for _ in range(100)]
            for thread in threads:
                thread.start()

            # wait for all threads to finish
            for thread in threads:
                thread.join()

            print(sys.getrefcount(lsa))
            print("done")
            time.sleep(30)
            memory_statistic.append(show_memory_info("Current"))
            current_time = int(time.time())

    def use_multi_dbs(self):
        # Q2 支持多数据库, support multiple databases, 测试完成
        from sqlalchemy import Integer, String, Column
        from sqlalchemy.orm import Mapped
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class Base2(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        class User2(Base2):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        # 定义数据库连接 URI
        db_config_dict = {
            'database1': {
                'url': get_config().DATABASE_URI,
                "model_class": Base,
                "engine_options": {},
                "session_options": {}
            },
            'database2': {
                'url': get_config().DATABASE_URI_1,
                "model_class": Base2,
                "engine_options": {},
                "session_options": {}
            }
        }

        start_time = int(time.time())
        db = LightSqlAlchemy(db_config=db_config_dict)

        # print("init engine: " + str(int(time.time()) - start_time))
        #
        # with db.get_non_flask_session() as session:
        #     print("init session: " + str(int(time.time()) - start_time))
        #     for i in range(30):
        #         new_user = User(username="d1", email="d1")
        #         session.add(new_user)
        #
        # with db.get_non_flask_session() as session:
        #     new_user = User2(username="d2", email="d2")
        #     session.add(new_user)
        #
        # print("done: " + str(int(time.time()) - start_time))

        def insert_d1():
            start_time = int(time.time())
            with db.get_db_session() as session:
                users = []
                for i in range(10):
                    new_user = User(username="d1", email="d1")
                    session.add(new_user)
                    # change to bulk
                #     users.append(new_user)
                # session.bulk_save_objects(users)
            # print("insert_d1: " + str(int(time.time()) - start_time))

        def insert_d2():
            start_time = int(time.time())
            with db.get_db_session() as session:
                users = []
                for i in range(10):
                    new_user = User2(username="d2", email="d2")
                    session.add(new_user)
                #     users.append(new_user)
                # session.bulk_save_objects(users)
            # print("insert_d2: " + str(int(time.time()) - start_time))

        start_time = int(time.time())
        end_time = start_time + 60 * 45

        # Test the worker function
        memory_statistic = []
        current_time = start_time

        # tracemalloc.start()
        # snapshot1 = tracemalloc.take_snapshot()
        count = 0
        while current_time < end_time:
            if current_time > start_time + 60 * 15 and current_time < start_time + 60 * 25:
                total = random.randint(1, 100)
            else:
                total = 100

            threads = [threading.Thread(target=insert_d1) for _ in range(total)]
            for thread in threads:
                thread.start()
            threads1 = [threading.Thread(target=insert_d2) for _ in range(40)]
            for thread in threads1:
                thread.start()

            # wait for all threads to finish
            for thread in threads:
                thread.join()
            for thread in threads1:
                thread.join()

            time.sleep(30)
            current_time = int(time.time())
            memory_statistic.append(show_memory_info("Current"))

        # snapshot2 = tracemalloc.take_snapshot()
        # top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        # print("[ Top 10 differences ]")
        # for stat in top_stats[:10]:
        #     print(stat)

    def flask_env_run(self):
        from sqlalchemy import Integer, String, Column
        from sqlalchemy.orm import Mapped
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class Base2(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        class User2(Base2):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        # 定义数据库连接 URI
        db_config_dict = {
            'database1': {
                'url': get_config().DATABASE_URI,
                "model_class": Base,
                "engine_options": {},
                "session_options": {}
            },
            'database2': {
                'url': get_config().DATABASE_URI_1,
                "model_class": Base2,
                "engine_options": {},
                "session_options": {}
            }
        }

        app = Flask(__name__)

        start_time = int(time.time())
        db = LightSqlAlchemy(is_flask=True)
        db.init_flask_app(app=app, db_config=db_config_dict)

        with app.app_context():
            print("init engine: " + str(int(time.time()) - start_time))
            session_id_in_same_thread = None
            with db.get_db_session() as session:
                session_id_in_same_thread = id(session)
                print("session: " + str(id(session)))
                print("init session: " + str(int(time.time()) - start_time))
                for i in range(10):
                    new_user = User(username="d1", email="d1")
                    session.add(new_user)

            session_id_1_in_same_thread = None
            with db.get_db_session() as session:
                session_id_1_in_same_thread = id(session)
                print("session: " + str(id(session)))
                print("init session: " + str(int(time.time()) - start_time))
                for i in range(10):
                    new_user = User2(username="d2", email="d2")
                    session.add(new_user)

            assert session_id_in_same_thread == session_id_1_in_same_thread
            print("session is reused")
            print("done: " + str(int(time.time()) - start_time))

    def flask_env_run_memory_lose(self):
        from sqlalchemy import Integer, String, Column
        from sqlalchemy.orm import Mapped
        from sqlalchemy.orm import DeclarativeBase

        class Base(DeclarativeBase):
            pass

        class Base2(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        class User2(Base2):
            __tablename__ = "user"

            id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
            username: Mapped[str] = Column(String(255), nullable=False)
            email: Mapped[str] = Column(String(255), nullable=False)

        # 定义数据库连接 URI
        db_config_dict = {
            'database1': {
                'url': get_config().DATABASE_URI,
                "model_class": Base,
                "engine_options": {},
                "session_options": {}
            },
            'database2': {
                'url': get_config().DATABASE_URI_1,
                "model_class": Base2,
                "engine_options": {},
                "session_options": {}
            }
        }

        app = Flask(__name__)

        db = LightSqlAlchemy(is_flask=True)
        db.init_flask_app(app=app, db_config=db_config_dict)

        start_time = int(time.time())
        end_time = start_time + 60 * 15

        # Test the worker function
        memory_statistic = []
        current_time = start_time
        while current_time < end_time:
            def insert_d1():
                # print("init engine: " + str(int(time.time()) - start_time))
                session_id_in_same_thread = None
                with app.app_context():
                    with db.get_db_session() as session:
                        session_id_in_same_thread = id(session)
                        # print("session: " + str(id(session)))
                        # print("init session: " + str(int(time.time()) - start_time))
                        for i in range(10):
                            new_user = User(username="d1", email="d1")
                            session.add(new_user)

            def insert_d2():
                session_id_1_in_same_thread = None
                with app.app_context():
                    with db.get_db_session() as session:
                        session_id_1_in_same_thread = id(session)
                        # print("session: " + str(id(session)))
                        # print("init session: " + str(int(time.time()) - start_time))
                        for i in range(10):
                            new_user = User2(username="d2", email="d2")
                            session.add(new_user)

            with app.app_context():
                threads = [threading.Thread(target=insert_d1) for _ in range(100)]
                for thread in threads:
                    thread.start()
                threads1 = [threading.Thread(target=insert_d2) for _ in range(40)]
                for thread in threads1:
                    thread.start()

                # wait for all threads to finish
                for thread in threads:
                    thread.join()
                for thread in threads1:
                    thread.join()

            time.sleep(30)
            current_time = int(time.time())
            memory_statistic.append(show_memory_info("Current"))


def read_and_write_spilting_in_non_flask():
    # Q6 测试读写分离
    from sqlalchemy import Integer, String, Column
    from sqlalchemy.orm import Mapped
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "user"

        id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
        username: Mapped[str] = Column(String(255), nullable=False)
        email: Mapped[str] = Column(String(255), nullable=False)

    # 定义数据库连接 URI
    db_config_dict = {
        'database1': {
            'url': get_config().DATABASE_URI,
            "model_class": Base,
            "engine_options": {},
            "session_options": {}
        },
        'database2': {
            'url': get_config().DATABASE_URI_2,
            "model_class": Base,
            "engine_options": {},
            "session_options": {},
            "db_operation_type": "read"
        }
    }

    db = LightSqlAlchemy(is_flask=False, db_config=db_config_dict, open_logging=True)

    def insert_d1():
        start_time = int(time.time())
        with db.get_db_session() as session:
            users = []
            for i in range(10):
                new_user = User(username="d1", email="d1")
                session.add(new_user)
    def insert_d2():
        start_time = int(time.time())
        with db.get_db_session("read") as session:
            users = []
            for i in range(10):
                new_user = User(username="d2", email="d2")
                session.add(new_user)

    start_time = int(time.time())
    end_time = start_time + 60 * 45

    # Test the worker function
    memory_statistic = []
    current_time = start_time

    while current_time < end_time:
        if current_time > start_time + 60 * 15 and current_time < start_time + 60 * 25:
            total = random.randint(1, 100)
        else:
            total = 2

        threads = [threading.Thread(target=insert_d1) for _ in range(total)]
        for thread in threads:
            thread.start()
        threads1 = [threading.Thread(target=insert_d2) for _ in range(2)]
        for thread in threads1:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()
        for thread in threads1:
            thread.join()

        time.sleep(30)
        current_time = int(time.time())
        memory_statistic.append(show_memory_info("Current"))


def read_and_write_spliting_in_flask():
    # Q6 测试读写分离
    from sqlalchemy import Integer, String, Column
    from sqlalchemy.orm import Mapped
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "user"

        id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
        username: Mapped[str] = Column(String(255), nullable=False)
        email: Mapped[str] = Column(String(255), nullable=False)

    # 定义数据库连接 URI
    db_config_dict = {
        'database1': {
            'url': get_config().DATABASE_URI,
            "model_class": Base,
            "engine_options": {},
            "session_options": {}
        },
        'database2': {
            'url': get_config().DATABASE_URI_2,
            "model_class": Base,
            "engine_options": {},
            "session_options": {},
            "db_operation_type": "read"
        }
    }

    app = Flask(__name__)
    db = LightSqlAlchemy(is_flask=True, open_logging=False)
    db.init_flask_app(app, db_config=db_config_dict)

    def insert_d1():
        start_time = int(time.time())
        with app.app_context():
            with db.get_db_session() as session:
                users = []
                for i in range(10):
                    new_user = User(username="d1", email="d1")
                    session.add(new_user)
    def insert_d2():
        start_time = int(time.time())
        with app.app_context():
            try:
                with db.get_db_session("read") as session:
                    users = []
                    for i in range(10):
                        new_user = User(username="d2", email="d2")
                        session.add(new_user)
            except Exception as e:
                print("insert d2 failed")

    start_time = int(time.time())
    end_time = start_time + 60 * 20

    # Test the worker function
    memory_statistic = []
    current_time = start_time

    while current_time < end_time:
        if current_time > start_time + 60 * 15 and current_time < start_time + 60 * 25:
            total = random.randint(1, 100)
        else:
            total = 2

        threads = [threading.Thread(target=insert_d1) for _ in range(total)]
        for thread in threads:
            thread.start()
        threads1 = [threading.Thread(target=insert_d2) for _ in range(2)]
        for thread in threads1:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()
        for thread in threads1:
            thread.join()

        time.sleep(30)
        current_time = int(time.time())
        memory_statistic.append(show_memory_info("Current"))

    print(memory_statistic)


if __name__ == '__main__':
    # Q1 non-flask
    # show_memory_info("Start")
    # TestLightSQLAlchemy().test_light_memory_lose_in_non_flask_env()
    # time.sleep(60)
    # show_memory_info("End")

    # Q2 one db
    # show_memory_info("Start")
    # TestLightSQLAlchemy().check_concurrent_with_one_db()
    # time.sleep(60)
    # show_memory_info("End")

    # Q3 multi dbs
    # show_memory_info("Start")
    # TestLightSQLAlchemy().use_multi_dbs()
    # time.sleep(60)
    # show_memory_info("End")

    # Q4 flask
    # show_memory_info("Start")
    # TestLightSQLAlchemy().flask_env_run()
    # time.sleep(60)
    # show_memory_info("End")

    # Q5 flask memory lose
    # show_memory_info("Start")
    # TestLightSQLAlchemy().flask_env_run_memory_lose()
    # time.sleep(60)
    # show_memory_info("End")

    # Q6 test read and write spilting
    # show_memory_info("Start")
    # read_and_write_spilting_in_non_flask()
    # time.sleep(60)
    # show_memory_info("End")

    # Q7 test read and write spilting in flask
    show_memory_info("Start")
    read_and_write_spliting_in_flask()
    time.sleep(60)
    show_memory_info("End")

    # import pytest
    # pytest.main(['-sv', 'tests/util_test/test_light_sqlalchemy.py'])
    #pytest.main(['test_area.py'])