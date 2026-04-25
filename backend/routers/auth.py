from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from passlib.context import CryptContext
from pymongo.errors import PyMongoError

from database import users_collection
from models.user import AuthResponse, UserLogin, UserRegister
from utils.auth import create_token

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister):
    email = user.email.lower()

    try:
        existing = users_collection.find_one({"email": email})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please try again later.",
        ) from exc

    if existing:
        raise HTTPException(status_code=400, detail="Email already exists.")

    hashed_password = pwd_context.hash(user.password)
    new_user = {
        "username": user.username,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = users_collection.insert_one(new_user)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not create your account right now.",
        ) from exc

    token = create_token(
        {"user_id": str(result.inserted_id), "username": user.username}
    )
    return AuthResponse(token=token, username=user.username)


@router.post("/login", response_model=AuthResponse)
async def login(user: UserLogin):
    email = user.email.lower()

    try:
        existing = users_collection.find_one({"email": email})
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Please try again later.",
        ) from exc

    if not existing:
        raise HTTPException(status_code=400, detail="User not found.")

    if not pwd_context.verify(user.password, existing["password"]):
        raise HTTPException(status_code=400, detail="Wrong password.")

    token = create_token(
        {"user_id": str(existing["_id"]), "username": existing["username"]}
    )
    return AuthResponse(token=token, username=existing["username"])
