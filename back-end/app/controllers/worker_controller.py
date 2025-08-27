from typing import List, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database import get_database
from app.schemas.worker import WorkerCreate, WorkerInDB, WorkerResponse, WorkerUpdate
from app.core.security import get_current_user

class WorkerController:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
            if self._db.client is None:
                self._db.connect_to_database()
        return self._db.client.fastapi_db.workers

    async def create_worker(self, worker: WorkerCreate, user_id: str) -> WorkerResponse:
        # Verify user exists and owns the worker
        if worker.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create worker for this user"
            )

        worker_dict = worker.model_dump()
        result = await self.db.insert_one(worker_dict)
        created_worker = await self.db.find_one({"_id": result.inserted_id})
        return WorkerResponse(**created_worker)

    async def get_user_workers(self, user_id: str) -> List[WorkerResponse]:
        workers = []
        cursor = self.db.find({"user_id": user_id})
        async for document in cursor:
            workers.append(WorkerResponse(**document))
        return workers

    async def get_worker(self, worker_id: str, user_id: str) -> WorkerResponse:
        if not ObjectId.is_valid(worker_id):
            raise HTTPException(status_code=400, detail="Invalid worker ID")

        worker = await self.db.find_one({"_id": ObjectId(worker_id)})
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if worker["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this worker"
            )

        return WorkerResponse(**worker)

    async def update_worker(self, worker_id: str, worker: WorkerUpdate, user_id: str) -> WorkerResponse:
        if not ObjectId.is_valid(worker_id):
            raise HTTPException(status_code=400, detail="Invalid worker ID")

        existing_worker = await self.db.find_one({"_id": ObjectId(worker_id)})
        if not existing_worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if existing_worker["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this worker"
            )

        update_data = worker.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")

        result = await self.db.update_one(
            {"_id": ObjectId(worker_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

        updated_worker = await self.db.find_one({"_id": ObjectId(worker_id)})
        return WorkerResponse(**updated_worker)

    async def delete_worker(self, worker_id: str, user_id: str) -> bool:
        if not ObjectId.is_valid(worker_id):
            raise HTTPException(status_code=400, detail="Invalid worker ID")

        worker = await self.db.find_one({"_id": ObjectId(worker_id)})
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        if worker["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this worker"
            )

        result = await self.db.delete_one({"_id": ObjectId(worker_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Worker not found")

        return True 