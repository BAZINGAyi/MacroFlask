import sqlalchemy as raw_sa
import sqlalchemy.event as raw_sa_event
import sqlalchemy.exc as raw_sa_exc
import sqlalchemy.orm as raw_sa_orm

from flask import Flask, g
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
        self.is_flask = is_flask

        # set logging
        self.open_logging = open_logging
        self.set_sqlalchemy_logging()
        self.set_logger(logger)

        # Init engines and sessions.
        # Read represents the read-only database, write represents the write-only or read-write database.
        self.engines = {"read": {}, "write": {}}
        self.sessions = {"read": None, "write": None}

        # bind base class to the engine
        self.bind_model_engines = {"read": {}, "write": {}}
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

        # Initialize the database engine for each bind key
        for bind_key, db_obj in db_config.items():
            if bind_key not in self.bind_key_models:
                raise ValueError(f"No model class registered for bind: {bind_key}")
            base_class = self.bind_key_models[bind_key]
            self._create_engine(**db_obj, base_class=base_class, bind_key=bind_key, **kwargs)

        # Binds engines to the Session
        self._make_session(**kwargs)

        # Register teardown function to ensure session is cleaned up at the end of each request.
        app.teardown_appcontext(self._teardown_session)

    def _teardown_session(self, exc: BaseException | None) -> None:
        """
        Clean up the session at the end of each request.

        :param exc: Any exception that might have occurred during request processing. Defaults to None.
        """
        db_operation_type = getattr(g, "session_db_operation_type", None)
        if db_operation_type:
            self.close_session(db_operation_type)

            # Remove the session_db_operation_type key from the Flask global context
            delattr(g, "session_db_operation_type")

    def _register_model(self, bind_key, model_class):
        """
        Register a model class for a specific bind key.

        :param bind_key: The bind key for the database.
        :param model_class: The model class to register.
        """
        self.bind_key_models[bind_key] = model_class

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
            self._create_engine(**db_obj, base_class=base_class, bind_key=bind_key, **kwargs)

        # Binds engines to the Session
        self._make_session(**kwargs)

    def _create_engine(self, url, base_class, bind_key, **kwargs):
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
            "pool_recycle": 4 * 60 * 60,
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
            if self.logger:
                self.logger.info("Connected to database: " + str(url))

        # Determine whether to read and write separately，
        db_operation_type = kwargs.get("db_operation_type", "write")
        # Configure the engine for the specified bind key
        self.engines[db_operation_type][bind_key] = engine
        # Configure the session binds
        self.bind_model_engines[db_operation_type][base_class] = engine

    def _make_session(self, **kwargs):
        """
        Create a new session instance for the specified bind key.

        :param bind_key: The bind key for the database.
        """
        # init session configuration
        session_options = {
            "autocommit": False,
            "autoflush": True,
            "expire_on_commit": True
        }

        if "session_options" in kwargs:
            session_options.update(kwargs.pop("session_options"))

        if self.bind_model_engines["read"]:
            if self.open_logging and self.logger:
                self.logger.info("Create read session.")
            read_session_local = sessionmaker(**session_options)
            # get the same session for the one same thread
            read_session = scoped_session(read_session_local)
            # Configure the session binds, one session for multiple databases
            read_session.configure(binds=self.bind_model_engines["read"])
            self.sessions["read"] = read_session

        if self.bind_model_engines["write"]:
            write_session_local = sessionmaker(**session_options)
            if self.open_logging and self.logger:
                self.logger.info("Create write session.")
            write_session = scoped_session(write_session_local)
            write_session.configure(binds=self.bind_model_engines["write"])
            self.sessions["write"] = write_session

    def _get_session(self, db_operation_type):
        """
        Retrieve the current thread's session instance.

        :param db_operation_type: The type of database operation.

        :return: The session instance for the current thread.

        :exception: ValueError if the session has not been initialized.
        """
        if not self.sessions[db_operation_type]:
            raise ValueError("Session has not been initialized.")
        if self.logger and self.open_logging:
            self.logger.info(f"Get {db_operation_type} session.")
        return self.sessions[db_operation_type]()

    @contextmanager
    def get_db_session(self, db_operation_type="write"):
        """
        Context manager for managing session lifecycle in Flask or non-Flask environments.

        :param db_operation_type: The type of database operation. Defaults to "write".

        :yield: The session instance for the current thread.
        """
        if self.is_flask:
            g.session_db_operation_type = db_operation_type

        session = self._get_session(db_operation_type)
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
                self.close_session(db_operation_type)  # Close the session and connections when the context ends

    def dispose_engine(self):
        """
        Dispose the engine and close all connections.

        :return: None
        """
        for engine in self.engines['read'].values():
            engine.dispose()

        for engine in self.engines['write'].values():
            engine.dispose()

    def close_session(self, db_operation_type):
        """
        :param db_operation_type: The type of database operation.

        Close the session and release the connection.

        :return: None
        """
        if self.logger and self.open_logging:
            self.logger.info(f"Close {db_operation_type} session.")

        if self.sessions[db_operation_type]:
            self.sessions[db_operation_type].remove()

    def set_sqlalchemy_logging(self):
        """
        Set up logging for SQLAlchemy to log all SQL queries.
        :return:
        """
        import logging
        logging.basicConfig()
        if self.open_logging:
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

                # Check db_operation_type
                db_operation_type = db_obj.get("db_operation_type")
                if db_operation_type and db_operation_type not in ["read", "write"]:
                    raise ValueError(f"db_operation_type must be 'read' or 'write' with key: {key}")

                # check db url
                if not db_obj.get("url"):
                    raise ValueError(f"url is required with key: {key}")

    def set_logger(self, logger):
        self.logger = logger
