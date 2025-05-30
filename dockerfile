FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && apt-get clean

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 9000