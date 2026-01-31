from app.database.config import SessionLocal
from app.database.models import User
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from endpoints.user import router as user_router

from . import schemas
from .database import engine, get_db, crud, Base

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(user_router)  # ← Add this line

Base.metadata.create_all(bind=engine)

# # Create user on first run
# db = SessionLocal()
# try:
#     user_data = schemas.UserCreate(
#         id="0",
#         name="John Doe",
#         karma=100,
#         maxVolume=0.8,
#         userType=1
#     )
#     crud.create_user(db, user_data)
# finally:
#     db.close()