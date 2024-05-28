FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

WORKDIR /app/
COPY ./requirements.txt /app/
COPY . /app/

RUN pip install -r requirements.txt
