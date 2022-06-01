from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class Role(str, Enum):
    admin = 'admin'
    user = 'user'


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Role = Role.user


class UserUpdate(UserBase):
    password: str


class User(UserBase):
    id: int
    disabled: bool = False


    class Config:
        orm_mode = True


class UserDesactivate(BaseModel):
    disabled: bool = True

    class Config:
        orm_mode = True


class Question(BaseModel):
    subject: str
    question: str
    responseA: str
    responseB: str
    responseC: Optional[str] = None
    responseD: Optional[str] = None

    class Config:
        orm_mode = True


class Answer(BaseModel):
    id: int
    question: str
    correct: str

    class Config:
        orm_mode = True


class AddQuestion(BaseModel):
    use: str
    subject: str
    question: str
    responseA: str
    responseB: str
    responseC: Optional[str] = None
    responseD: Optional[str] = None
    correct: str
    remark: Optional[str] = None

    class Config:
        orm_mode = True


class Subject(str, Enum):
    bdd = "BDD"
    system = "Systèmes distribués"
    streaming = "Streaming de données"
    data = "Data Science"
    docker = "Docker"
    classification = "Classification"
    ml = "Machine Learning"
    auto = "Automation"


class Use(str, Enum):
    pos = "Test de positionnement"
    val = "Test de validation"
    boot = "Total Bootcamp"


class Nbquestion(str, Enum):
    nb5 = "5"
    nb10 = "10"
    nb20 = "20"


'''
    subject: str
    correct: str
    use: str
    responseA: str
    responseB: str
    responseC: Optional[str] = None
    responseD: Optional[str] = None
    remark: Optional[str] = None
'''
