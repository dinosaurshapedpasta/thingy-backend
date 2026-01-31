from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .db import engine, get_db

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"Hello": "World"}

@app.post("/users", response_model=schemas.UserRead)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/api-keys", response_model=schemas.ApiKeyRead)
def create_api_key(api_key: schemas.ApiKeyCreate, db: Session = Depends(get_db)):
    return crud.create_api_key(db, api_key)


@app.get("/api-keys/{user_id}/{key_hash}", response_model=schemas.ApiKeyRead)
def get_api_key(user_id: str, key_hash: str, db: Session = Depends(get_db)):
    db_api_key = crud.get_api_key(db, user_id, key_hash)
    if db_api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return db_api_key


@app.post("/item-variants", response_model=schemas.ItemVariantRead)
def create_item_variant(
    item_variant: schemas.ItemVariantCreate, db: Session = Depends(get_db)
):
    return crud.create_item_variant(db, item_variant)


@app.get("/item-variants/{item_variant_id}", response_model=schemas.ItemVariantRead)
def get_item_variant(item_variant_id: str, db: Session = Depends(get_db)):
    db_item_variant = crud.get_item_variant(db, item_variant_id)
    if db_item_variant is None:
        raise HTTPException(status_code=404, detail="Item variant not found")
    return db_item_variant


@app.post("/pickup-points", response_model=schemas.PickupPointRead)
def create_pickup_point(
    pickup_point: schemas.PickupPointCreate, db: Session = Depends(get_db)
):
    return crud.create_pickup_point(db, pickup_point)


@app.get("/pickup-points/{pickup_point_id}", response_model=schemas.PickupPointRead)
def get_pickup_point(pickup_point_id: str, db: Session = Depends(get_db)):
    db_pickup_point = crud.get_pickup_point(db, pickup_point_id)
    if db_pickup_point is None:
        raise HTTPException(status_code=404, detail="Pickup point not found")
    return db_pickup_point


@app.post("/storage-points", response_model=schemas.StoragePointRead)
def create_storage_point(
    storage_point: schemas.StoragePointCreate, db: Session = Depends(get_db)
):
    return crud.create_storage_point(db, storage_point)


@app.get("/storage-points/{storage_point_id}", response_model=schemas.StoragePointRead)
def get_storage_point(storage_point_id: str, db: Session = Depends(get_db)):
    db_storage_point = crud.get_storage_point(db, storage_point_id)
    if db_storage_point is None:
        raise HTTPException(status_code=404, detail="Storage point not found")
    return db_storage_point


@app.post("/drop-off-points", response_model=schemas.DropOffPointRead)
def create_drop_off_point(
    drop_off_point: schemas.DropOffPointCreate, db: Session = Depends(get_db)
):
    return crud.create_drop_off_point(db, drop_off_point)


@app.get("/drop-off-points/{drop_off_point_id}", response_model=schemas.DropOffPointRead)
def get_drop_off_point(drop_off_point_id: str, db: Session = Depends(get_db)):
    db_drop_off_point = crud.get_drop_off_point(db, drop_off_point_id)
    if db_drop_off_point is None:
        raise HTTPException(status_code=404, detail="Drop-off point not found")
    return db_drop_off_point


@app.post("/items-at-pickup-point", response_model=schemas.ItemsAtPickupPointRead)
def create_items_at_pickup_point(
    record: schemas.ItemsAtPickupPointCreate, db: Session = Depends(get_db)
):
    return crud.create_items_at_pickup_point(db, record)


@app.get(
    "/items-at-pickup-point/{pickup_point_id}/{item_variant_id}",
    response_model=schemas.ItemsAtPickupPointRead,
)
def get_items_at_pickup_point(
    pickup_point_id: str, item_variant_id: str, db: Session = Depends(get_db)
):
    db_record = crud.get_items_at_pickup_point(db, pickup_point_id, item_variant_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record


@app.post("/items-in-car", response_model=schemas.ItemsInCarRead)
def create_items_in_car(
    record: schemas.ItemsInCarCreate, db: Session = Depends(get_db)
):
    return crud.create_items_in_car(db, record)


@app.get(
    "/items-in-car/{user_id}/{item_variant_id}",
    response_model=schemas.ItemsInCarRead,
)
def get_items_in_car(
    user_id: str, item_variant_id: str, db: Session = Depends(get_db)
):
    db_record = crud.get_items_in_car(db, user_id, item_variant_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record


@app.post("/items-in-storage", response_model=schemas.ItemsInStorageRead)
def create_items_in_storage(
    record: schemas.ItemsInStorageCreate, db: Session = Depends(get_db)
):
    return crud.create_items_in_storage(db, record)


@app.get(
    "/items-in-storage/{storage_id}/{item_variant_id}",
    response_model=schemas.ItemsInStorageRead,
)
def get_items_in_storage(
    storage_id: str, item_variant_id: str, db: Session = Depends(get_db)
):
    db_record = crud.get_items_in_storage(db, storage_id, item_variant_id)
    if db_record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return db_record


