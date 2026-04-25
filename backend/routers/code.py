from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from pymongo.errors import PyMongoError

from database import sessions_collection
from utils.ai_helper import (
    get_bug_fix,
    get_code_completion,
    get_code_explanation,
)
from utils.auth import verify_token

router = APIRouter()
security = HTTPBearer(auto_error=False)


class CodeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)

    code: str = Field(min_length=1, max_length=50000)
    language: str = Field(min_length=1, max_length=40)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authorization token.")

    return verify_token(credentials.credentials)


def store_session(user_id: str, action_type: str, request: CodeRequest, result: str) -> None:
    try:
        sessions_collection.insert_one(
            {
                "user_id": user_id,
                "type": action_type,
                "code": request.code,
                "result": result,
                "language": request.language,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except PyMongoError:
        # AI actions should still work even if history storage is temporarily unavailable.
        return


@router.post("/complete")
async def complete_code(
    request: CodeRequest,
    user_id: str = Depends(get_current_user_id),
):
    result = get_code_completion(request.code, request.language)
    store_session(user_id, "completion", request, result)
    return {"result": result}


@router.post("/fix")
async def fix_code(
    request: CodeRequest,
    user_id: str = Depends(get_current_user_id),
):
    result = get_bug_fix(request.code, request.language)
    store_session(user_id, "fix", request, result)
    return {"result": result}


@router.post("/explain")
async def explain_code(
    request: CodeRequest,
    user_id: str = Depends(get_current_user_id),
):
    result = get_code_explanation(request.code, request.language)
    store_session(user_id, "explanation", request, result)
    return {"result": result}


@router.get("/history")
async def get_history(
    limit: int = Query(default=10, ge=1, le=25),
    user_id: str = Depends(get_current_user_id),
):
    try:
        sessions = list(
            sessions_collection.find({"user_id": user_id}, {"_id": 0})
            .sort("created_at", -1)
            .limit(limit)
        )
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not load session history.",
        ) from exc

    return {"history": sessions}
