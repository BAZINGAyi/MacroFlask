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

from sqlalchemy.orm import sessionmaker, scoped_session


# class LightSqlAlchemyOld:
#     def __init__(self, flask_app):
#         # self.db_uri = db_uri
#         # self.engine = create_engine(db_uri)
#         # self.session = sessionmaker(bind=self.engine)
#
#         session_options = {}
#         self.session = self._make_scoped_session(session_options)
#
#     def _make_scoped_session(
#         self, options: dict[str, typing.Any]
#     ) -> raw_sa_orm.scoped_session[Session]:
#         """Create a :class:`sqlalchemy.orm.scoping.scoped_session` around the factory
#         from :meth:`_make_session_factory`. The result is available as :attr:`session`.
#
#         The scope function can be customized using the ``scopefunc`` key in the
#         ``session_options`` parameter to the extension. By default it uses the current
#         thread or greenlet id.
#
#         This method is used for internal setup. Its signature may change at any time.
#
#         :meta private:
#
#         :param options: The ``session_options`` parameter from ``__init__``. Keyword
#             arguments passed to the session factory. A ``scopefunc`` key is popped.
#
#         .. versionchanged:: 3.0
#             The session is scoped to the current app context.
#
#         .. versionchanged:: 3.0
#             Renamed from ``create_scoped_session``, this method is internal.
#         """
#         # scope = options.pop("scopefunc", _app_ctx_id)
#         factory = self._make_session_factory(options)
#         return raw_sa_orm.scoped_session(factory)
#
#     def _make_session_factory(
#         self, options: dict[str, typing.Any]
#     ) -> raw_sa_orm.sessionmaker[Session]:
#         """Create the SQLAlchemy :class:`sqlalchemy.orm.sessionmaker` used by
#         :meth:`_make_scoped_session`.
#
#         To customize, pass the ``session_options`` parameter to :class:`SQLAlchemy`. To
#         customize the session class, subclass :class:`.Session` and pass it as the
#         ``class_`` key.
#
#         This method is used for internal setup. Its signature may change at any time.
#
#         :meta private:
#
#         :param options: The ``session_options`` parameter from ``__init__``. Keyword
#             arguments passed to the session factory.
#
#         .. versionchanged:: 3.0
#             The session class can be customized.
#
#         .. versionchanged:: 3.0
#             Renamed from ``create_session``, this method is internal.
#         """
#         # options.setdefault("class_", Session)
#         # options.setdefault("query_cls", self.Query)
#         return raw_sa_orm.sessionmaker(db=self, **options)
#
#     def _teardown_session(self, exc: BaseException | None) -> None:
#         """Remove the current session at the end of the request.
#
#         :meta private:
#
#         .. versionadded:: 3.0
#         """
#         self.session.remove()
#
#     def _make_engine(
#         self, bind_key: str | None, options: dict[str, typing.Any], app
#     ) -> raw_sa.engine.Engine:
#         """Create the :class:`sqlalchemy.engine.Engine` for the given bind key and app.
#
#         To customize, use :data:`.SQLALCHEMY_ENGINE_OPTIONS` or
#         :data:`.SQLALCHEMY_BINDS` config. Pass ``engine_options`` to :class:`SQLAlchemy`
#         to set defaults for all engines.
#
#         This method is used for internal setup. Its signature may change at any time.
#
#         :meta private:
#
#         :param bind_key: The name of the engine being created.
#         :param options: Arguments passed to the engine.
#         :param app: The application that the engine configuration belongs to.
#
#         .. versionchanged:: 3.0
#             Renamed from ``create_engine``, this method is internal.
#         """
#         return raw_sa.engine_from_config(options, prefix="")
#
#     def return_scoped_session(self):
#         url = "sqlite:///:memory:"
#         engine = raw_sa.create_engine(url)
#         SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
#         Session = scoped_session(SessionLocal)
#         return Session


from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, scoped_session


from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager


class LightSqlAlchemy:
    def __init__(self, app=None, db_url=None, **kwargs):
        """
        Initialize the LightSqlAlchemy object.

        :param uri: Database connection URI, used only in non-Flask environments.
        :param app: Flask application instance, used only in Flask environments.
        """
        self.engine = None
        self.session_local = None
        self.session = None

        if app:
            self._init_app(app)

        else:
            if not db_url:
                raise ValueError("Database URI must be provided for non-Flask environments.")
            self._init_non_flask_env(db_url, **kwargs)

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

    def _init_non_flask_env(self, url: str, **kwargs):
        """
        Initialize for non-Flask environments with database engine and session configuration.

        :param url: Database connection URI.
        :param kwargs: Additional keyword arguments for creating the engine.
        """
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
            "pool_timeout": 30,  # 增加连接超时时间（秒）
            # reset the timeout of idle connections in the connection pool (seconds)
            "pool_recycle": 2 * 60 * 60,  # 重置连接池中的空闲连接的超时时间（秒）
        }
        if "engine_options" in kwargs:
            options.update(kwargs.pop("engine_options"))
        self.engine = create_engine(url, **engine_options)

        # init session configuration
        session_options = {
            "autocommit": False,
            "autoflush": True,
            "expire_on_commit": True
        }
        if "session_options" in kwargs:
            session_options.update(kwargs.pop("session_options"))
        self.session_local = sessionmaker(bind=self.engine, **session_options)
        self.session = scoped_session(self.session_local)

    def get_session(self):
        """
        Retrieve the current thread's session instance.

        :return: The session instance for the current thread.
        """
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
        self.session.remove()


if __name__ == '__main__':
    # Q1 100 并发，没有内存泄露的问题,
    # SELECT * FROM information_schema.PROCESSLIST where ID NOT IN (6472, 8759, 8841);
    # 测试 memory 占用

    # Q2 支持多数据库

    # Q3 了解 weakref

    # Q4 增加监听器，用于 debug

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




