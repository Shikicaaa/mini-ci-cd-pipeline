from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
EXPIRATION_HOURS = 26


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now() + timedelta(hours=EXPIRATION_HOURS)
    to_encode.update(
        {"exp": expire}
    )
    encoded = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return encoded


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
