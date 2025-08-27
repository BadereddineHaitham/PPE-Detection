from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router
from app.database import db
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="FastAPI Backend",
    description="A well-structured FastAPI backend server",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database connection
@app.on_event("startup")
async def startup_db_client():
    db.connect_to_database(os.getenv("MONGODB_URL"))

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close_database_connection()

# Include routers
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 