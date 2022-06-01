FROM python:3.8.12-slim-buster

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8000

CMD [ "uvicorn", "api:app", "--host", "0.0.0.0"]
