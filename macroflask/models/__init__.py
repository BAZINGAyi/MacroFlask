from datetime import datetime

from sqlalchemy import Integer, Column, DateTime, Text
from sqlalchemy.orm import DeclarativeBase
from macroflask.util.light_sqlalchemy import LightSqlAlchemy

"""
Config database details:

1. config db_config_dict

2. create db instance for global use
"""


class Base(DeclarativeBase):
    __abstract__ = True  # This is an abstract class, not a table


class CommonModelMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    description = Column(Text())


db = LightSqlAlchemy(is_flask=True, open_logging=True)
