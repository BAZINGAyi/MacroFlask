from sqlalchemy.orm import DeclarativeBase
from macroflask.util.light_sqlalchemy import LightSqlAlchemy

"""
Config database details:

1. config db_config_dict

2. create db instance for global use
"""


class Base(DeclarativeBase):
    pass


db = LightSqlAlchemy(is_flask=True)
