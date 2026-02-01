from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class UserCreate(BaseModel):
    id: str
    name: str
    karma: int
    maxVolume: float
    userType: int


class UserRead(UserCreate):
    model_config = {"from_attributes": True}


class ApiKeyCreate(BaseModel):
    userID: str
    keyHash: str


class ApiKeyRead(ApiKeyCreate):
    model_config = {"from_attributes": True}


class ItemVariantCreate(BaseModel):
    id: str
    name: str
    volume: float


class ItemVariantRead(ItemVariantCreate):
    model_config = {"from_attributes": True}


class PickupPointCreate(BaseModel):
    id: str
    name: str
    location: str


class PickupPointRead(PickupPointCreate):
    model_config = {"from_attributes": True}


class PickupRequest(BaseModel):
    id: str
    pickupPointID: str


class StoragePointCreate(BaseModel):
    id: str
    name: str
    maxVolume: float
    location: str


class StoragePointRead(StoragePointCreate):
    model_config = {"from_attributes": True}


class DropOffPointCreate(BaseModel):
    id: str
    name: str
    location: str


class DropOffPointRead(DropOffPointCreate):
    model_config = {"from_attributes": True}


class ItemsAtPickupPointCreate(BaseModel):
    pickupPointID: str
    itemVariantID: str
    quantity: int


class ItemsAtPickupPointRead(ItemsAtPickupPointCreate):
    model_config = {"from_attributes": True}


class ItemsInCarCreate(BaseModel):
    userID: str
    itemVariantID: str
    quantity: int


class ItemsInCarRead(ItemsInCarCreate):
    model_config = {"from_attributes": True}


class ItemsInStorageCreate(BaseModel):
    storageID: str
    itemVariantID: str
    quantity: int


class ItemsInStorageRead(ItemsInStorageCreate):
    model_config = {"from_attributes": True}


class StorageItemResponse(BaseModel):
    id: str
    quantity: int


# ============== Auction Schemas ==============

class AuctionCreate(BaseModel):
    pickupRequestID: str


class AuctionRead(BaseModel):
    id: str
    pickupRequestID: str
    status: str
    createdAt: datetime
    expiresAt: datetime
    winnerUserID: Optional[str] = None
    
    model_config = {"from_attributes": True}


class AuctionBidCreate(BaseModel):
    """Volunteer's response to an auction."""
    accepted: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AuctionBidRead(BaseModel):
    auctionID: str
    userID: str
    accepted: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    estimatedTime: Optional[float] = None
    score: Optional[float] = None
    createdAt: datetime
    
    model_config = {"from_attributes": True}


class AuctionResult(BaseModel):
    """Result of an auction after processing."""
    auctionID: str
    winnerUserID: Optional[str] = None
    bids: List[AuctionBidRead]


class RoutingInput(BaseModel):
    """Input data for the routing algorithm."""
    distance_matrix: List[List[float]]  # Volunteers to drop-off points
    drops_matrix: List[List[float]]      # Between drop-off points
    item_volumes: List[float]            # Volume of each item
    car_caps: List[float]                # Capacity of each volunteer's car
    volunteer_ids: List[str]             # IDs of participating volunteers
    dropoff_ids: List[str]               # IDs of drop-off points
    car_contents: List[List[float]]      # Current contents of each car (volume per item type)
    item_id: str                         # ID of the item variant being delivered
