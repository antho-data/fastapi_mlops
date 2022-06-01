import pyotp
from sqlalchemy.orm import Session

import models
import schemas
from security import pwd_context


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        otp_secret=pyotp.random_base32(),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_to_modify: str,
                user_update: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.username == user_to_modify).first()
    db_user.email = user_update.email
    db_user.username = user_update.username
    db_user.full_name = user_update.full_name
    db_user.hashed_password = pwd_context.hash(user_update.password)
    db.commit()
    db.refresh(db_user)
    return db_user


def desactivate_user(db: Session, user_to_desactivate: str,
                     disable: schemas.UserDesactivate):
    db_user = db.query(models.User).filter(models.User.username == user_to_desactivate).first()
    db_user.disabled = disable.disabled
    db.commit()
    db.refresh(db_user)
    return db_user


def create_question(db: Session, qa: schemas.AddQuestion):
    """
    :param db: Session
    :param qa: Schemas
    :return: db
    """
    db_question = models.Question(
        question=qa.question,
        subject=qa.subject,
        correct=qa.correct,
        use=qa.use,
        responseA=qa.responseA,
        responseB=qa.responseB,
        responseC=qa.responseC,
        responseD=qa.responseD,
        remark=qa.remark
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


'''
def update_user(db: Session, user_update: schemas.UserUpdate):
    db_user = user_update.id
    db_user.email = user_update.email
    db_user.username = user_update.username
    db_user.full_name = user_update.full_name
    db_user.hashed_password = pwd_context.hash(user_update.password)
    db_user.disabled = user_update.disabled
    db.commit()
    db.refresh(db_user)
    return db_user
'''
