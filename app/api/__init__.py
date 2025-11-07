from fastapi import APIRouter

from app.api import utils, auth, users, reported_phones

api_router = APIRouter()

api_router.include_router(utils.router, tags=["utils"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(reported_phones.router, tags=["reported_phones"])
