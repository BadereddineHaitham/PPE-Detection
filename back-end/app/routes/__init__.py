from fastapi import APIRouter
from .auth_routes import router as auth_router
from .camera_routes import router as camera_router
from .worker_routes import router as worker_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["authentication"])
router.include_router(camera_router, prefix="/cameras", tags=["cameras"])
router.include_router(worker_router, prefix="/workers", tags=["workers"])