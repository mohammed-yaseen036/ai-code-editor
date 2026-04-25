from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import JWTError, jwt

from config import get_settings

ALGORITHM = "HS256"


def create_token(data: dict) -> str:
    settings = get_settings()
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    settings = get_settings()

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication payload.")

    return user_id
