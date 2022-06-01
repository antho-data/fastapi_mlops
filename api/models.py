from sqlalchemy import Boolean, Column, Integer, String, Enum, VARCHAR

from database import Base
from schemas import Role


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    otp_secret = Column(String)
    disabled = Column(Boolean, default=False)
    role = Column(Enum(Role))


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = {"sqlite_autoincrement": True}

    id = Column(Integer, primary_key=True, nullable=False)
    question = Column(String, unique=True)
    subject = Column(String)
    correct = Column(VARCHAR(4))
    use = Column(String)
    responseA = Column(String)
    responseB = Column(String)
    responseC = Column(String)
    responseD = Column(String)
    remark = Column(String)
