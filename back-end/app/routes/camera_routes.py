from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.controllers.camera_controller import CameraController
from app.schemas.camera import CameraCreate, CameraResponse, CameraUpdate
from app.core.security import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()
camera_controller = CameraController()

@router.post("/", response_model=CameraResponse)
async def create_camera(
    camera: CameraCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new camera for the current user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await camera_controller.create_camera(camera, current_user.id)

@router.get("/", response_model=List[CameraResponse])
async def get_user_cameras(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all cameras for the current user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await camera_controller.get_user_cameras(current_user.id)

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific camera by ID"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await camera_controller.get_camera(camera_id, current_user.id)

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: str,
    camera: CameraUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a specific camera"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await camera_controller.update_camera(camera_id, camera, current_user.id)

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a specific camera"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await camera_controller.delete_camera(camera_id, current_user.id)