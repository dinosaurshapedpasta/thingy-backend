from typing import List

from sqlalchemy.orm import Session

from . import models
from .. import schemas
from .repository import (
    user_repo,
    api_key_repo,
    item_variant_repo,
    pickup_point_repo,
    pickup_request_repo,
    pickup_request_responses_repo,
    storage_point_repo,
    dropoff_point_repo,
    items_at_pickup_repo,
    items_in_car_repo,
    items_in_storage_repo,
)


# User CRUD - Now 3 lines instead of 30
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    return user_repo.create(db, user)


def get_user(db: Session, user_id: str) -> models.User | None:
    return user_repo.get_by_id(db, user_id)


def update_user(
    db: Session, user_id: str, user_update: schemas.UserCreate
) -> models.User | None:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    return user_repo.update(db, db_user, user_update)


# ApiKey CRUD
def create_api_key(db: Session, api_key: schemas.ApiKeyCreate) -> models.ApiKey:
    return api_key_repo.create(db, api_key)


def get_api_key(db: Session, user_id: str, key_hash: str) -> models.ApiKey | None:
    return api_key_repo.get_by_keys(db, user_id, key_hash)


# ItemVariant CRUD
def create_item_variant(
    db: Session, item_variant: schemas.ItemVariantCreate
) -> models.ItemVariant:
    return item_variant_repo.create(db, item_variant)


def get_item_variant(db: Session, item_variant_id: str) -> models.ItemVariant | None:
    return item_variant_repo.get_by_id(db, item_variant_id)


def update_item_variant(
    db: Session, item_variant_id: str, variant_update: schemas.ItemVariantCreate
) -> models.ItemVariant | None:
    db_variant = get_item_variant(db, item_variant_id)
    if not db_variant:
        return None
    return item_variant_repo.update(db, db_variant, variant_update)


# PickupPoint CRUD
def create_pickup_point(
    db: Session, pickup_point: schemas.PickupPointCreate
) -> models.PickupPoint:
    return pickup_point_repo.create(db, pickup_point)


def get_pickup_point(db: Session, pickup_point_id: str) -> models.PickupPoint | None:
    return pickup_point_repo.get_by_id(db, pickup_point_id)


def update_pickup_point(
    db: Session, pickup_point_id: str, point_update: schemas.PickupPointCreate
) -> models.PickupPoint | None:
    db_point = get_pickup_point(db, pickup_point_id)
    if not db_point:
        return None
    return pickup_point_repo.update(db, db_point, point_update)


# PickupRequest CRUD
def get_active_pickup_requests(db: Session) -> List[schemas.PickupRequest]:
    return db.query(models.PickupRequest).all()


def create_pickup_request(
    db: Session, pickup_request: schemas.PickupRequest
) -> models.PickupRequest:
    return pickup_request_repo.create(db, pickup_request)


def delete_pickup_request(db: Session, id: str) -> bool:
    """Delete a pickup request and its associated responses."""
    pickup_request = pickup_request_repo.get_by_id(db, id)
    if not pickup_request:
        return False

    # Delete associated responses first (foreign key constraint)
    db.query(models.PickupRequestResponses).filter(
        models.PickupRequestResponses.requestID == id
    ).delete()

    db.delete(pickup_request)
    db.commit()
    return True


def get_pickup_request_responses(
    db: Session, id: str
) -> List[models.PickupRequestResponses]:
    return (
        db.query(models.PickupRequestResponses)
        .filter(models.PickupRequestResponses.requestID == id)
        .all()
    )


def create_pickup_request_response(
    db: Session, id: str, current_user_id: str, resp: int
) -> bool:
    """Record volunteer response to pickup request."""
    # Check if request exists
    pickup_request = pickup_request_repo.get_by_id(db, id)
    if not pickup_request:
        return False

    # Check if response already exists
    response = pickup_request_responses_repo.get_by_keys(db, id, current_user_id)

    if response:
        # Update existing response
        response.result = resp
        db.commit()
    else:
        # Create new response
        new_response = models.PickupRequestResponses(
            requestID=id, userID=current_user_id, result=resp
        )
        db.add(new_response)
        db.commit()

    return True


# StoragePoint CRUD
def create_storage_point(
    db: Session, storage_point: schemas.StoragePointCreate
) -> models.StoragePoint:
    return storage_point_repo.create(db, storage_point)


def get_storage_point(
    db: Session, storage_point_id: str
) -> models.StoragePoint | None:
    return storage_point_repo.get_by_id(db, storage_point_id)


def update_storage_point(
    db: Session, storage_point_id: str, point_update: schemas.StoragePointCreate
) -> models.StoragePoint | None:
    db_point = get_storage_point(db, storage_point_id)
    if not db_point:
        return None
    return storage_point_repo.update(db, db_point, point_update)


# DropOffPoint CRUD
def create_drop_off_point(
    db: Session, drop_off_point: schemas.DropOffPointCreate
) -> models.DropOffPoint:
    return dropoff_point_repo.create(db, drop_off_point)


def get_drop_off_point(
    db: Session, drop_off_point_id: str
) -> models.DropOffPoint | None:
    return dropoff_point_repo.get_by_id(db, drop_off_point_id)


def update_drop_off_point(
    db: Session, drop_off_point_id: str, point_update: schemas.DropOffPointCreate
) -> models.DropOffPoint | None:
    db_point = get_drop_off_point(db, drop_off_point_id)
    if not db_point:
        return None
    return dropoff_point_repo.update(db, db_point, point_update)


# ItemsAtPickupPoint CRUD
def create_items_at_pickup_point(
    db: Session, record: schemas.ItemsAtPickupPointCreate
) -> models.ItemsAtPickupPoint:
    return items_at_pickup_repo.create(db, record)


def get_items_at_pickup_point(
    db: Session, pickup_point_id: str, item_variant_id: str
) -> models.ItemsAtPickupPoint | None:
    return items_at_pickup_repo.get_by_keys(db, pickup_point_id, item_variant_id)


def get_all_items_at_pickup_point(
    db: Session, pickup_point_id: str
) -> list[models.ItemsAtPickupPoint]:
    return items_at_pickup_repo.filter_by(db, {"pickupPointID": pickup_point_id})


def update_items_at_pickup_point(
    db: Session, pickup_point_id: str, item_variant_id: str, quantity: int
) -> models.ItemsAtPickupPoint | None:
    """Update the quantity of items at a pickup point."""
    db_record = get_items_at_pickup_point(db, pickup_point_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity
    db.commit()
    db.refresh(db_record)
    return db_record


# ItemsInCar CRUD
def create_items_in_car(
    db: Session, record: schemas.ItemsInCarCreate
) -> models.ItemsInCar:
    return items_in_car_repo.create(db, record)


def get_items_in_car(
    db: Session, user_id: str, item_variant_id: str
) -> models.ItemsInCar | None:
    return items_in_car_repo.get_by_keys(db, user_id, item_variant_id)


def update_items_in_car(
    db: Session, user_id: str, item_variant_id: str, quantity: int
) -> models.ItemsInCar | None:
    """Update the quantity of items in a user's car."""
    db_record = get_items_in_car(db, user_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity
    db.commit()
    db.refresh(db_record)
    return db_record


# ItemsInStorage CRUD
def create_items_in_storage(
    db: Session, record: schemas.ItemsInStorageCreate
) -> models.ItemsInStorage:
    return items_in_storage_repo.create(db, record)


def get_items_in_storage(
    db: Session, storage_id: str, item_variant_id: str
) -> models.ItemsInStorage | None:
    return items_in_storage_repo.get_by_keys(db, storage_id, item_variant_id)


def update_items_in_storage(
    db: Session, storage_id: str, item_variant_id: str, quantity: int
) -> models.ItemsInStorage | None:
    """Update the quantity of items in storage."""
    db_record = get_items_in_storage(db, storage_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity
    db.commit()
    db.refresh(db_record)
    return db_record
