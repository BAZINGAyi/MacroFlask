import gc
import sys
import threading
import time
import tracemalloc
import typing
from contextlib import contextmanager

import sqlalchemy as raw_sa
import sqlalchemy.event as raw_sa_event
import sqlalchemy.exc as raw_sa_exc
import sqlalchemy.orm as raw_sa_orm
from flask import Flask

import os
import psutil

from config import get_config


# 显示当前 python 程序占用的内存大小
def show_memory_info(hint):
    pid = os.getpid()
    p = psutil.Process(pid)

    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    print('{} memory used: {} MB'.format(hint, memory))


from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager


class LightSqlAlchemy:
    def __init__(self, db_config: dict, app=None, **kwargs):
        """
        Initialize the LightSqlAlchemy object.

        :param uri: Database connection URI, used only in non-Flask environments.
        :param app: Flask application instance, used only in Flask environments.
        """
        self.engine = None
        self.session_local = None
        self.session = None

        # bind base class to the engine
        self.bind_model_engines = {}
        self.bind_key_models = {}

        # check db config parameter
        if isinstance(db_config, dict) and db_config:
            for key, db_obj in db_config.items():
                # register key model
                if not db_obj.get("model_class"):
                    raise ValueError(f"model_class is required")
                self._register_model(key, db_obj["model_class"])

                # check db url
                if not db_obj.get("url"):
                    raise ValueError(f"url is required with key: {key}")

        if app:
            self._init_app(app)

        else:
            self._init_non_flask_env(db_config, **kwargs)

    def _init_app(self, app: Flask):
        """
        Initialize Flask application with database engine and session configuration.

        :param app: Flask application instance.
        """
        self.engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = scoped_session(self.session_local)

        # Register teardown function to ensure session is cleaned up at the end of each request.
        app.teardown_appcontext(self._teardown_session)

    def _teardown_session(self, exc: BaseException | None) -> None:
        """
        Clean up the session at the end of each request.

        :param exc: Any exception that might have occurred during request processing. Defaults to None.
        """
        self.close_session()

    def _register_model(self, bind, model_class):
        """
        Register a model class for a specific bind key.

        :param bind: The bind key for the database.
        :param model_class: The model class to register.
        """
        self.bind_key_models[bind] = model_class

    def _configure_session_binds(self, base_class, engine):
        """
        Configure the session binds to automatically use the correct engine based on the base class.
        """
        if self.session:
            self.bind_model_engines[base_class] = engine
            self.session.configure(binds=self.bind_model_engines)

    def _init_non_flask_env(self, db_config: dict, **kwargs):
        """
        Initialize for non-Flask environments with database engine and session configuration.

        :param url: Database connection URI.
        :param kwargs: Additional keyword arguments for creating the engine.
        """
        for bind_key, db_obj in db_config.items():
            if bind_key not in self.bind_key_models:
                raise ValueError(f"No model class registered for bind: {bind_key}")
            base_class = self.bind_key_models[bind_key]
            self._create_engine_and_session(**db_obj, base_class=base_class, **kwargs)

    def _create_engine_and_session(self, url, base_class, **kwargs):
        url = raw_sa.engine.make_url(url)
        if not url.drivername.startswith("mysql"):
            raise ValueError(
                "MySQL database is required for non-Flask environments,"
                " other databases are not supported.")

        # init engine configuration
        engine_options = {
            # increase the number of connections in the pool
            "pool_size": 50,
            # increase the number of connections that can be created when the pool is empty
            "max_overflow": 100,
            # number of seconds to wait before giving up on getting a connection from the pool
            "pool_timeout": 30,
            # reset the timeout of idle connections in the connection pool (seconds)
            "pool_recycle": 2 * 60 * 60,
        }
        if "engine_options" in kwargs:
            engine_options.update(kwargs.pop("engine_options"))
        engine = create_engine(url, **engine_options)

        # init session configuration
        session_options = {
            "autocommit": False,
            "autoflush": True,
            "expire_on_commit": True
        }
        if "session_options" in kwargs:
            session_options.update(kwargs.pop("session_options"))
        session_local = sessionmaker(bind=self.engine, **session_options)
        self.session = scoped_session(session_local)

        # Configure the session binds
        self._configure_session_binds(base_class, engine)

    def get_session(self):
        """
        Retrieve the current thread's session instance.

        :return: The session instance for the current thread.

        :exception: ValueError if the session has not been initialized.
        """
        if not self.session:
            raise ValueError("Session has not been initialized.")
        return self.session()
    @contextmanager
    def get_flask_session(self):
        """
        Context manager for managing session lifecycle in Flask environments.

        :yield: The session instance for the current thread.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()  # Commit the transaction
        except Exception as e:
            session.rollback()  # Rollback the transaction in case of an exception
            raise e  # Re-raise the exception

    @contextmanager
    def get_non_flask_session(self):
        """
        Context manager for managing session lifecycle in non-Flask environments.

        :yield: The session instance for the current thread.
        """
        session = self.get_session()
        try:

            yield session
            session.commit()  # Commit the transaction

        except Exception as e:

            session.rollback()  # Rollback the transaction in case of an exception
            raise e  # Re-raise the exception

        finally:
            self.close_session()  # Close the session and connections when the context ends

    def dispose_engine(self):
        """
        Dispose the engine and close all connections.

        :return: None
        """
        self.dispose_engine()

    def close_session(self):
        """
        Close the session and release the connection.

        :return: None
        """
        if self.session:
            self.session.remove()


def check_concurrent_with_one_db():
    # Q1 100 并发，没有内存泄露的问题,
    # SELECT * FROM information_schema.PROCESSLIST where ID NOT IN (6472, 8759, 8841);
    # SHOW VARIABLES LIKE 'max_connections';
    # 测试 memory 占用

    from sqlalchemy import Integer, String, Column
    from sqlalchemy.orm import Mapped, sessionmaker
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "user"

        id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
        username: Mapped[str] = Column(String(255), nullable=False)
        email: Mapped[str] = Column(String(255), nullable=False)

    # none-flask environment
    url = get_config().DATABASE_URI
    engine_options = {
        # "pool_size": 5,  # 增大连接池大小
        # "max_overflow": 1,  # 增大溢出连接数
        # "pool_timeout": 1,  # 增加连接超时时间（秒）
        # "pool_recycle": 5,  # 重置连接池中的空闲连接的超时时间（秒）
    }
    options = {
        "engine_options": engine_options
    }
    lsa = LightSqlAlchemy(db_url=url, **options)

    def worker():
        with lsa.get_non_flask_session() as session:
            # Perform database operations
            # print("session-id" + str(id(session)))
            users = session.query(User).all()
            for user in users:
                # print(user.username)
                pass

    while True:
        show_memory_info("Current")

        threads = [threading.Thread(target=worker) for _ in range(100)]
        for thread in threads:
            thread.start()

        # wait for all threads to finish
        for thread in threads:
            thread.join()

        print(sys.getrefcount(lsa))
        print("done")
        time.sleep(30)

def use_multi_dbs():
    # Q2 支持多数据库, support multiple databases, 测试完成
    from sqlalchemy import Integer, String, Column
    from sqlalchemy.orm import Mapped, sessionmaker
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
        with db.get_non_flask_session() as session:
            users = []
            for i in range(1):
                new_user = User(username="d1", email="d1")
                # session.add(new_user)
                # change to bulk
                users.append(new_user)
            session.bulk_save_objects(users)
        print("insert_d1: " + str(int(time.time()) - start_time))

    def insert_d2():
        start_time = int(time.time())
        with db.get_non_flask_session() as session:
            users = []
            for i in range(1):
                new_user = User2(username="d2", email="d2")
                # session.add(new_user)
                users.append(new_user)
            session.bulk_save_objects(users)
        print("insert_d2: " + str(int(time.time()) - start_time))

    while True:
        show_memory_info("Current")

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


if __name__ == '__main__':

    # Q3 了解 weakref

    # Q4 增加监听器，用于 debug

    from sqlalchemy import Integer, String, Column
    from sqlalchemy.orm import Mapped, sessionmaker
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

    print("init engine: " + str(int(time.time()) - start_time))

    with db.get_non_flask_session() as session:
        print("init session: " + str(int(time.time()) - start_time))
        for i in range(30):
            new_user = User(username="d1", email="d1")
            session.add(new_user)

    with db.get_non_flask_session() as session:
        new_user = User2(username="d2", email="d2")
        session.add(new_user)

    print("done: " + str(int(time.time()) - start_time))





