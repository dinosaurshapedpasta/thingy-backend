from app.database.config import SessionLocal
from app.database.models import User
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from endpoints.user import router as user_router
from endpoints.default import router as default_router

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

app.include_router(user_router)
app.include_router(default_router)

Base.metadata.create_all(bind=engine)
