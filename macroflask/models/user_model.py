from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker

from macroflask.models import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = Column(String(255), nullable=False)
    email: Mapped[str] = Column(String(255), nullable=False)
