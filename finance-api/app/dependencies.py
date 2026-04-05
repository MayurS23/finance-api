from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_access_token
from app.database import get_db
from app.models import Role, User, UserStatus

bearer_scheme = HTTPBearer()


# ── Get current user from JWT ──────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if user.status == UserStatus.inactive:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return user


# ── Role-based guards ──────────────────────────────────────────────────────────

# Role hierarchy: viewer (1) < analyst (2) < admin (3)
_ROLE_LEVEL: dict[Role, int] = {
    Role.viewer:  1,
    Role.analyst: 2,
    Role.admin:   3,
}


def require_role(*roles: Role):
    """
    Returns a dependency that ensures the current user's role is
    at least as permissive as one of the given roles.

    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(Role.admin))])
    """
    min_level = min(_ROLE_LEVEL[r] for r in roles)

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        if _ROLE_LEVEL[current_user.role] < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied — requires one of: {', '.join(r.value for r in roles)}",
            )
        return current_user

    return _check


# Convenience shorthands
require_viewer  = require_role(Role.viewer)    # any authenticated user
require_analyst = require_role(Role.analyst)   # analyst or admin
require_admin   = require_role(Role.admin)     # admin only
