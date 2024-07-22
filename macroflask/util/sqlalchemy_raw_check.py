import os
import sys
import threading
import time

import psutil
from sqlalchemy import Integer, String, Column, create_engine
from sqlalchemy.orm import Mapped, sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase


def show_memory_info(hint):
    pid = os.getpid()
    p = psutil.Process(pid)

    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    print('{} memory used: {} MB'.format(hint, memory))


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = Column(String(255), nullable=False)
    email: Mapped[str] = Column(String(255), nullable=False)


options = {
    "pool_size": 5,  # 增大连接池大小
    "max_overflow": 1,  # 增大溢出连接数
    "pool_timeout": 1,  # 增加连接超时时间（秒）
    "pool_recycle": 5,  # 重置连接池中的空闲连接的超时时间（秒）
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
        engine = create_engine(url="mysql+pymysql://root:MyNewPass1!@10.124.44.192:3306/ethan_db", **options)
        with Session(engine) as session:
            # print(id(session))
            users = session.query(User).all()
            for user in users:
                # print(user.username)
                pass

        # with Session(engine) as session:
        #     # print(id(session))
        #     users = session.query(User).all()
        #     for user in users:
        #         # print(user.username)
        #         pass

        while True:
            show_memory_info("Current")

            threads = [threading.Thread(target=worker) for _ in range(10)]
            for thread in threads:
                thread.start()

            # wait for all threads to finish
            for thread in threads:
                thread.join()

            print(sys.getrefcount(engine))
            print("done")
            time.sleep(30)