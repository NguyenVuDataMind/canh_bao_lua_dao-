from fastapi import APIRouter

from app.api import utils, auth, users, reported_phones, image_processing, whitelist, reports, admin, sos

api_router = APIRouter()

api_router.include_router(utils.router, tags=["utils"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(reported_phones.router, tags=["reported_phones"])
api_router.include_router(image_processing.router, tags=["image_processing"])
api_router.include_router(whitelist.router, tags=["whitelist"])
api_router.include_router(reports.router, tags=["reports"])
api_router.include_router(admin.router, tags=["admin"])
api_router.include_router(sos.router, tags=["sos"])
