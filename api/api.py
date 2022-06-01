import secrets
from typing import List

from fastapi import FastAPI, Depends, HTTPException, Query, status, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import pandas as pd

from models import Question, Subject, Use

app = FastAPI(title="QCM questions API")

security = HTTPBasic()

USERS = {
    "bob": {"password": "builder", "role": "user"},
    "alice": {"password": "wonderland", "role": "user"},
    "clementine": {"password": "mandarine", "role": "user"},
    "admin": {"password": "4dm1N", "role": "admin"},
}

questions = pd.read_csv("questions.csv")


def get_current_user_info(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username not in USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = USERS[credentials.username]

    if not secrets.compare_digest(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return {"username": credentials.username, "role": user["role"]}

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/questions", response_model=List[Question])
async def get_questions(
    use: Use,
    subjects: List[Subject] = Query(None),
    n_questions: int = 5,
    user: any = Depends(get_current_user_info),
):

    selected_questions = questions.loc[
        (questions.use == use)
        & questions.subject.isin([subject.value for subject in subjects])
    ]

    if len(selected_questions) > n_questions:
        selected_questions = selected_questions.sample(n_questions)

    return [v.dropna().to_dict() for k, v in selected_questions.iterrows()]


@app.post("/questions")
async def get_questions(question: Question, user: any = Depends(get_current_user_info)):

    if user["role"] != "admin":
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    global questions
    questions = pd.concat([questions, pd.DataFrame([question.dict()])])

    questions.to_csv("questions.csv", index=False)

    return Response("Created", status_code=201)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
