from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from passlib.context import CryptContext
from .repo_model import repo_user

pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(unhashed_pass, hashed_pass) -> bool:
    return pwd_context.verify(unhashed_pass, hashed_pass)


class User(Base):
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, unique=True, index=True)
    email: str = Column(String, unique=True, index=True)
    password_hash: str = Column(String)

    tests = relationship("Test", back_populates="owner")
    configs = relationship("RepoConfig", secondary=repo_user, back_populates="users")


class Test(Base):
    __tablename__ = "tests"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String)
    result: str = Column(String)
    user_id: int = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="tests")
