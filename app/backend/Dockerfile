FROM python:3.9-slim-buster

RUN apt-get update && apt-get -y install libpq-dev gcc

# install dependencies
#RUN apt-get update && apt-get install -y apt-transport-https libssl-dev libffi-dev gcc python3-dev musl-dev \
    #build-essential libpq-dev netcat-openbsd

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/app

WORKDIR /usr/src

ENTRYPOINT ["python", "worker.py"]
