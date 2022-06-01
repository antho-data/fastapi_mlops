from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import func
from starlette import status
from starlette.responses import JSONResponse, RedirectResponse

import pandas as pd

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
import crud
import models
import schemas

from database import SessionLocal, engine

from security import pwd_context

models.Base.metadata.create_all(bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

DESCRIPTION = """
QCM API helps you do awesome stuff. 🚀

## QCM

Generate random QCM. Connected to a DB 
Make your own unique QCM

## Users

* **Generate QCM** 
* **Get Answer** 
* **Read your own information** 

## Admin area

* **Create and remove Users** (roles implemented: User/Admin).
* **Create new questions** 
* **Upload CSV to database** 
* **Update User informations and password** 
* **Activate / Disable User** 

## TODO

* **Update your informations and reset password** (_not implemented_).
* **Multi Factor Authentication** (_not implemented_).
* **HTML render forms** (_not implemented_).

"""

tags_metadata = [
    {
        "name": "token access",
        "description": "Public access to generate token access",
    },
    {
        "name": "QCM",
        "description": "User QCM access and answer",
    },
    {
        "name": "Informations",
        "description": "Users informations",
    },
    {
        "name": "Users management / admin area",
        "description": "Operations with users",
    },
    {
        "name": "Update question database / Danger ZONE: Reset table Question",
        "description": "Update database with CSV or manually",
    },
]

app = FastAPI(
    title="QCM api for beginners",
    description=DESCRIPTION,
    version="0.1.5",
    contact={
        "name": "antho-data",
        "url": "https://github.com/",
        "email": "contact@datacientest.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    openapi_tags=tags_metadata
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db: Session, username: str):
    return crud.get_user_by_username(db, username)


"""
def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password[:-6], user.hashed_password):
        return False
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(password[-6:]):
        return False
    return user
"""


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: schemas.User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_admin_user(
    current_user: schemas.User = Depends(get_current_active_user),
):
    if current_user.role != schemas.Role.admin:
        raise HTTPException(status_code=400, detail="User has insufficient permissions")
    return current_user


@app.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url='/docs')


@app.post("/token", response_model=schemas.Token, tags=["token access"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=schemas.User, tags=["Informations"])
async def read_users_me(current_user: schemas.User = Depends(get_current_active_user)):
    return current_user


@app.post("/users/", response_model=schemas.User, tags=["Users management / admin area"])
def create_new_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user),
):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User or mail already exist"
        )
    else:
        db_user = crud.create_user(db, user)
        return db_user


@app.put("/users/update/", response_model=schemas.User, tags=["Users management / admin area"])
async def user_update_record(user_to_modify: str,
                       user_update: schemas.UserUpdate,
                       db: Session = Depends(get_db),
                       current_user: schemas.User = Depends(get_current_active_admin_user)):
    db_user = db.query(models.User).filter(models.User.username == user_update.username).first()
    if db_user is not None or user_to_modify == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Can't update user {user_update.username}, already exist in db or You can't modify admin"
        )
    else:
        db_user = crud.update_user(db, user_to_modify, user_update)
        return db_user


@app.put("/users/deactivate/", response_model=schemas.User, tags=["Users management / admin area"])
async def user_desactivate(user_to_desactivate: str,
                           user_disabled: schemas.UserDesactivate,
                       db: Session = Depends(get_db),
                       current_user: schemas.User = Depends(get_current_active_admin_user)):
    db_user = db.query(models.User).filter(models.User.username == user_to_desactivate).first()
    if db_user is None or user_to_desactivate == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Can't disable user {user_to_desactivate}, not exist in db"
        )
    else:
        db_user = crud.desactivate_user(db, user_to_desactivate, user_disabled)
        return db_user


@app.delete("/users/delete/{username}", tags=["Users management / admin area"])
async def user_delete(
    username: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None or username == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="User doesn't Exist / You can't remove admin",
        )
    db.delete(db_user)
    db.commit()
    return {"removed": username}


@app.get("/users/list", response_model=List[schemas.User],  tags=["Users management / admin area"])
async def get_list_db_users(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user),
):
    db_user = crud.get_users(db)
    return db_user


@app.get(
    "/qcm/{use}/{subject}/{nb_questions}",
    tags=["QCM"],
    response_model=List[schemas.Question],
)
async def qcm_utilisateur(
    use: schemas.Use,
    subject: schemas.Subject,
    nb_questions: schemas.Nbquestion,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    SQL_Query = (
        db.query(models.Question)
        .filter(models.Question.use == use, models.Question.subject == subject)
        .order_by(func.random())
        .limit(int(nb_questions))
        .all()
    )

    return SQL_Query


@app.get("/qcm/{question_id}", tags=["QCM"], response_model=schemas.Answer)
async def qcm_response(
    question_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    SQL_Query = (
        db.query(models.Question).filter(models.Question.id == question_id).first()
    )

    return SQL_Query


@app.post("/db_reset/", tags=["Update question database / Danger ZONE: Reset table Question"])
def reset_database(
    current_user: schemas.User = Depends(get_current_active_admin_user),
    db: Session = Depends(get_db)
):
    db.query(models.Question).delete()
    db.commit()
    with open("./data/questions.csv", "r", encoding="utf-8") as file:
        data_df = pd.read_csv(file)
    data_df.to_sql(
        "questions",
        con=engine,
        index=True,
        index_label="id",
        if_exists="append",
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content="Table question updated"
    )


@app.post("/qcm_add/", response_model=schemas.AddQuestion, tags=["Update question database / Danger ZONE: Reset table Question"])
def add_question_to_database(
    qa: schemas.AddQuestion,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_active_admin_user),
):
    db_qa = crud.create_question(db, qa)
    return db_qa


"""
@app.post('/subject_choose')
def form_post(request: Request,
              num: int = Form(...),
              multiply_by_2: bool = Form(False),
              current_user: schemas.User = Depends(get_current_active_user)):
    return templates.TemplateResponse('index.html', context={'request': request, 'result': result, 'num': num})
"""
