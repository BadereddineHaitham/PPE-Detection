from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.controllers.worker_controller import WorkerController
from app.schemas.worker import WorkerCreate, WorkerResponse, WorkerUpdate
from app.core.security import get_current_user
from app.schemas.user import UserResponse

router = APIRouter()
worker_controller = WorkerController()

@router.post("/", response_model=WorkerResponse)
async def create_worker(
    worker: WorkerCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new worker for the current user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await worker_controller.create_worker(worker, current_user.id)

@router.get("/", response_model=List[WorkerResponse])
async def get_user_workers(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get all workers for the current user"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await worker_controller.get_user_workers(current_user.id)

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get a specific worker by ID"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await worker_controller.get_worker(worker_id, current_user.id)

@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: str,
    worker: WorkerUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a specific worker"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await worker_controller.update_worker(worker_id, worker, current_user.id)

@router.delete("/{worker_id}")
async def delete_worker(
    worker_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a specific worker"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return await worker_controller.delete_worker(worker_id, current_user.id) 