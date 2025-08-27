from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database import get_database
from app.schemas.camera import CameraCreate, CameraInDB, CameraResponse, CameraUpdate
from app.core.security import get_current_user

class CameraController:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
            if self._db.client is None:
                self._db.connect_to_database()
        return self._db.client.fastapi_db.cameras

    async def create_camera(self, camera: CameraCreate, user_id: str) -> CameraResponse:
        # Verify user exists and owns the camera
        if camera.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create camera for this user"
            )

        camera_dict = camera.model_dump()
        result = await self.db.insert_one(camera_dict)
        created_camera = await self.db.find_one({"_id": result.inserted_id})
        return CameraResponse(**created_camera)

    async def get_user_cameras(self, user_id: str) -> List[CameraResponse]:
        cameras = []
        cursor = self.db.find({"user_id": user_id})
        async for document in cursor:
            cameras.append(CameraResponse(**document))
        return cameras

    async def get_camera(self, camera_id: str, user_id: str) -> CameraResponse:
        if not ObjectId.is_valid(camera_id):
            raise HTTPException(status_code=400, detail="Invalid camera ID")

        camera = await self.db.find_one({"_id": ObjectId(camera_id)})
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        if camera["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this camera"
            )

        return CameraResponse(**camera)

    async def update_camera(self, camera_id: str, camera: CameraUpdate, user_id: str) -> CameraResponse:
        if not ObjectId.is_valid(camera_id):
            raise HTTPException(status_code=400, detail="Invalid camera ID")

        existing_camera = await self.db.find_one({"_id": ObjectId(camera_id)})
        if not existing_camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        if existing_camera["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this camera"
            )

        update_data = camera.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")

        result = await self.db.update_one(
            {"_id": ObjectId(camera_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        updated_camera = await self.db.find_one({"_id": ObjectId(camera_id)})
        return CameraResponse(**updated_camera)

    async def delete_camera(self, camera_id: str, user_id: str) -> bool:
        if not ObjectId.is_valid(camera_id):
            raise HTTPException(status_code=400, detail="Invalid camera ID")

        camera = await self.db.find_one({"_id": ObjectId(camera_id)})
        if not camera:
            raise HTTPException(status_code=404, detail="Camera not found")

        if camera["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this camera"
            )

        result = await self.db.delete_one({"_id": ObjectId(camera_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Camera not found")

        return True 