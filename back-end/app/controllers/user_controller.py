from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
from app.database import get_database, Database
from app.schemas.user import UserCreate, UserInDB, UserResponse
from app.core.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta

class UserController:
    def __init__(self):
        self._db: Optional[Database] = None

    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
            if self._db.client is None:
                self._db.connect_to_database()
        return self._db.client.fastapi_db.users

    async def create_user(self, user: UserCreate) -> UserResponse:
        # Check if user already exists
        existing_user = await self.db.find_one({"email": user.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user
        hashed_password = get_password_hash(user.password)
        user_dict = user.model_dump(exclude={"password"})
        user_dict["hashed_password"] = hashed_password
        user_dict["is_active"] = True
        user_dict["is_superuser"] = False

        result = await self.db.insert_one(user_dict)
        created_user = await self.db.find_one({"_id": result.inserted_id})
        return UserResponse(**created_user)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        user = await self.db.find_one({"email": email})
        if not user:
            return None
        if not verify_password(password, user["hashed_password"]):
            return None
        return UserInDB(**user)

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        user = await self.db.find_one({"email": email})
        if not user:
            return None
        return UserInDB(**user)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        user = await self.db.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        return UserInDB(**user)

    async def update_user(self, user_id: str, user_data: dict) -> UserResponse:
        if not ObjectId.is_valid(user_id):
            raise HTTPException(status_code=400, detail="Invalid user ID")

        update_data = {k: v for k, v in user_data.items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")

        result = await self.db.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        updated_user = await self.db.find_one({"_id": ObjectId(user_id)})
        return UserResponse(**updated_user) 