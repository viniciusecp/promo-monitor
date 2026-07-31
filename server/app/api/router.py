from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.api.routes import (
    auth,
    health,
    interests,
    matcher,
    matches,
    messages,
    settings,
    telegram_auth,
    users,
)

api_router = APIRouter()
api_router.include_router(health.public_router)
api_router.include_router(auth.router)

protected = APIRouter(dependencies=[Depends(require_user)])
protected.include_router(health.router)
protected.include_router(interests.router)
protected.include_router(matcher.router)
protected.include_router(matches.router)
protected.include_router(messages.router)
protected.include_router(settings.router)
protected.include_router(telegram_auth.router)
protected.include_router(users.router)

api_router.include_router(protected)
