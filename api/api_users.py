from fastapi import APIRouter, Body, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from db import SessionLocal
from models.user_model import User, hash_password, verify_password
from auth.jwt_handler import create_token, decode_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
        authorization: str = Header(...),
        db: Session = Depends(get_db)
) -> User | None:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not valid bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Invalid or expired token"
        )
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain sub",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    username: str = Body(...),
    email: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username or User.email == email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with that email or username already exists!"
        )
    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "User registered successfully!"
    }


@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    email: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email: '{email}' doesn't exist"
        )
    elif not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect!"
        )
    token = create_token({
        "sub": user.username
    })
    return {
        "access_token": token,
        "token_type": "bearer"
    }
