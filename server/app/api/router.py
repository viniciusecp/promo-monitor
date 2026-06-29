from fastapi import APIRouter

from app.api.routes import (
    health,
    interests,
    matcher,
    matches,
    messages,
    settings,
    telegram,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(interests.router)
api_router.include_router(matcher.router)
api_router.include_router(matches.router)
api_router.include_router(messages.router)
api_router.include_router(settings.router)
api_router.include_router(telegram.router)
