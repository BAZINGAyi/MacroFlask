import sqlalchemy as raw_sa
import sqlalchemy.event as raw_sa_event
import sqlalchemy.exc as raw_sa_exc
import sqlalchemy.orm as raw_sa_orm

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager


class LightSqlAlchemy:
    def __init__(self, is_flask=False, db_config: dict = None, open_logging=False, logger=None, **kwargs):
        """
        Initialize the LightSqlAlchemy object.

        :param is_flask: Whether the environment is a Flask application. Defaults to False.
        :param db_config: Database configuration dictionary. Defaults to None.
        :param open_logging: Whether to enable logging for SQLAlchemy. Defaults to False.
        """
        # set logging
        self.is_flask = is_flask
        self.set_sqlalchemy_logging(open_logging)
        self.set_logger(logger)

        self.engine = None
        self.session_local = None
        self.session = None

        # bind base class to the engine
        self.bind_model_engines = {}
        self.bind_key_models = {}

        if is_flask:
            pass

        else:
            self.validate_db_config(db_config)
            self._init_non_flask_env(db_config, **kwargs)

    def init_flask_app(self, app: Flask, db_config: dict, **kwargs):
        """
        Initialize Flask application with database engine and session configuration.

        :param app: Flask application instance.
        :param db_config: Database configuration dictionary.
        """
        if not self.is_flask:
            raise ValueError("Flask environment is not enabled.")

        self.validate_db_config(db_config)

        for bind_key, db_obj in db_config.items():
            if bind_key not in self.bind_key_models:
                raise ValueError(f"No model class registered for bind: {bind_key}")
            base_class = self.bind_key_models[bind_key]
            self._create_engine_and_session(**db_obj, base_class=base_class, **kwargs)

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
            # isolation level for the engine
            "isolation_level": "READ COMMITTED",
            # enable the echo mode for debugging
            "echo": False,
            # enable the echo mode for the connection pool, input 'debug' if you want to debug
            "echo_pool": False,
            # enable the pool pre-ping to test connections before using them
            # "pool_pre_ping": False,
        }
        if "engine_options" in kwargs:
            engine_options.update(kwargs.pop("engine_options"))
        engine = create_engine(url, **engine_options)
        with engine.connect():
            self.logger.info("Connected to database: " + str(url))

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

    def _get_session(self):
        """
        Retrieve the current thread's session instance.

        :return: The session instance for the current thread.

        :exception: ValueError if the session has not been initialized.
        """
        if not self.session:
            raise ValueError("Session has not been initialized.")
        return self.session()

    @contextmanager
    def get_db_session(self):
        """
        Context manager for managing session lifecycle in Flask or non-Flask environments.

        :yield: The session instance for the current thread.
        """
        session = self._get_session()
        try:

            yield session
            session.commit()  # Commit the transaction

        except Exception as e:

            session.rollback()  # Rollback the transaction in case of an exception
            raise e  # Re-raise the exception

        finally:

            # if current env is not flask, close the session.
            # Otherwise, the session will be closed by Flask
            if not self.is_flask:
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

    @staticmethod
    def set_sqlalchemy_logging(open_logging: bool):
        """
        Set up logging for SQLAlchemy to log all SQL queries.
        :return:
        """
        import logging
        logging.basicConfig()
        if open_logging:
            logging.getLogger('sqlalchemy.echo').setLevel(logging.INFO)
            logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
            logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    def validate_db_config(self, db_config: dict):
        """
        Validate the database configuration dictionary.
        :param db_config: The database configuration dictionary.
        :return:
        """
        if not isinstance(db_config, dict) or not db_config:
            raise ValueError("db_config must be a non-empty dictionary.")

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

    def set_logger(self, logger):
        self.logger = logger
