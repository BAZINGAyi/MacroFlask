import os
import sys
import threading
import time

import psutil
from sqlalchemy import Integer, String, Column, create_engine
from sqlalchemy.orm import Mapped, sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase

from config import get_config


def show_memory_info(hint):
    pid = os.getpid()
    p = psutil.Process(pid)

    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    print('{} memory used: {} MB'.format(hint, memory))
    return memory


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = Column(String(255), nullable=False)
    email: Mapped[str] = Column(String(255), nullable=False)


options = {
            # increase the number of connections in the pool
            "pool_size": 50,
            # increase the number of connections that can be created when the pool is empty
            "max_overflow": 100,
            # number of seconds to wait before giving up on getting a connection from the pool
            "pool_timeout": 30,
            # reset the timeout of idle connections in the connection pool (seconds)
            "pool_recycle": 2 * 60 * 60,
            # isolation level for the engine
            "isolation_level": "READ COMMITTED",
            # enable the echo mode for debugging
            "echo": False,
            # enable the echo mode for the connection pool, input 'debug' if you want to debug
            "echo_pool": False,
            # enable the pool pre-ping to test connections before using them
            # "pool_pre_ping": False,
        }


def check_insert_performance():
    start_time = int(time.time())
    engine = create_engine(url="mysql+pymysql://root:MyNewPass1!@10.124.44.192:3306/ethan_db", **options)
    with Session(engine) as session:
        print("init session: " + str(int(time.time()) - start_time))
        for i in range(1):
            new_user = User(username="d1", email="d1")
            session.add(new_user)
        print("add done: " + str(int(time.time()) - start_time))
        session.commit()
    print("init done: " + str(int(time.time()) - start_time))


def check_memory_leak():
    def worker():
        with Session(engine) as session:
            # print(id(session))
            # users = session.query(User).all()
            # for user in users:
            #     # print(user.username)
            #     pass
            user = session.query(User).where().first()
            username = user.username

        # with Session(engine) as session:
        #     # print(id(session))
        #     users = session.query(User).all()
        #     for user in users:
        #         # print(user.username)
        #         pass

    engine = create_engine(url=get_config().DATABASE_URI, **options)
    start_time = int(time.time())
    end_time = start_time + 60 * 5
    current_time = start_time
    memory_statistic = []
    while current_time < end_time:
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for thread in threads:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()

        print(sys.getrefcount(engine))
        print("done")
        time.sleep(30)
        current_time = int(time.time())
        memory_statistic.append(show_memory_info("Current"))
    print(memory_statistic)


if __name__ == '__main__':
    show_memory_info("Start")
    check_memory_leak()
    show_memory_info("End")
    # check_inse    rt_performance()