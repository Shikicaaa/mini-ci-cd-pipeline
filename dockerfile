FROM python:3.11-slim

ARG BUILD_DATE
ARG COMMIT_SHA

LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$COMMIT_SHA

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install flake8 pytest

RUN flake8 . || exit 1

RUN pytest tests/ || exit 1

CMD ["python", "main.py"]
