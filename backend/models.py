from sqlalchemy import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Tuple
from sqlalchemy import Enum
import enum

class StatusEnum(enum.Enum):
        IN_PROGRESS = 0
        WAITING = 1
        DENIED = 2
        APPROVED = 3

class Base(DeclarativeBase):
    pass

class Corners(Base):
    __tablename__ = 'corners'

    id: Mapped[int] = mapped_column(primary_key=True)
    x1: Mapped[float] = mapped_column()
    y1: Mapped[float] = mapped_column()
    x2: Mapped[float] = mapped_column()
    y2: Mapped[float] = mapped_column()
    x3: Mapped[float] = mapped_column()
    y3: Mapped[float] = mapped_column()
    x4: Mapped[float] = mapped_column()
    y4: Mapped[float] = mapped_column()
    

class Session(Base):
    __tablename__ = 'sessions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    corners: Mapped[Corners] = mapped_column()
    consistent_count: Mapped[int] = mapped_column()
    previous_size: Mapped[Tuple[int, int]] = mapped_column()
    status: Mapped[StatusEnum] = mapped_column(Enum(StatusEnum))

    corners = Mapped[Corners] = relationship('Corners', back_populates='session', cascade='all, delete-orphan')