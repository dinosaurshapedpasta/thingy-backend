from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.user import router as user_router
from endpoints.item import router as item_router
from endpoints.pickup import router as pickup_router
from endpoints.storage import router as storage_router
from endpoints.dropoff import router as dropoff_router
from endpoints.pickuprequests import router as pickuprequests_router
from endpoints.default import router as default_router
from endpoints.auction import router as auction_router

from .database import engine, Base

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(default_router)
app.include_router(user_router)
app.include_router(item_router)
app.include_router(pickup_router)
app.include_router(storage_router)
app.include_router(dropoff_router)
app.include_router(pickuprequests_router)
app.include_router(auction_router)

Base.metadata.create_all(bind=engine)
