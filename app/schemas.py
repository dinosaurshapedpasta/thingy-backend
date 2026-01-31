from pydantic import BaseModel


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
