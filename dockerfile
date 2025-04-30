FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dodaj lint i test alate
RUN pip install flake8 pytest

# Run lint
RUN flake8 . || exit 1

# Run tests
RUN pytest tests/ || exit 1

CMD ["python", "main.py"]