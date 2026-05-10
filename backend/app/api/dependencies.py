from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services import auth_service
from ..models.user import User
from ..config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    settings = get_settings()

    # Check API key first (for FL clients)
    api_key = request.headers.get("X-API-Key")
    if api_key and api_key == settings.CLIENT_API_KEY:
        # Return the admin user (or first active user) for API key clients
        result = await db.execute(
            select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1)
        )
        user = result.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No active user found")

    # Fall back to JWT Bearer token
    if credentials:
        user = await auth_service.get_current_user_from_token(credentials.credentials, db, settings)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")
        return user

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
