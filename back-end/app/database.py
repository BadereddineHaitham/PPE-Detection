from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Database:
    client: Optional[AsyncIOMotorClient] = None
    
    def connect_to_database(self, path: str = None):
        try:
            if path:
                self.client = AsyncIOMotorClient(path)
            else:
                # Default to localhost if no path provided
                self.client = AsyncIOMotorClient("mongodb://localhost:27017")
            print("Connected to MongoDB.")
        except Exception as e:
            print(f"Could not connect to MongoDB: {e}")
    
    def close_database_connection(self):
        try:
            self.client.close()
            print("Closed connection with MongoDB.")
        except Exception as e:
            print(f"Could not close MongoDB connection: {e}")

# Create a database instance
db = Database()

# Get database instance
def get_database() -> Database:
    return db 