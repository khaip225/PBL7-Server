from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas.auth import LoginRequest, TokenResponse, UserResponse
from ..services import auth_service
from .dependencies import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    from ..config import get_settings
    token = auth_service.create_access_token(user.id, get_settings())
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
