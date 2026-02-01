from typing import List

from sqlalchemy.orm import Session

from . import models
from .. import schemas


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, user_id: str) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()


def update_user(
    db: Session, user_id: str, user_update: schemas.UserCreate
) -> models.User | None:
    """Update a user's details (excluding ID)."""
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    # Update fields (ignore ID)
    db_user.name = user_update.name
    db_user.karma = user_update.karma
    db_user.maxVolume = user_update.maxVolume
    db_user.userType = user_update.userType

    db.commit()
    db.refresh(db_user)
    return db_user


def create_api_key(db: Session, api_key: schemas.ApiKeyCreate) -> models.ApiKey:
    db_api_key = models.ApiKey(**api_key.model_dump())
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key


def get_api_key(db: Session, user_id: str, key_hash: str) -> models.ApiKey | None:
    return (
        db.query(models.ApiKey)
        .filter(
            models.ApiKey.userID == user_id,
            models.ApiKey.keyHash == key_hash,
        )
        .first()
    )


def create_item_variant(
    db: Session, item_variant: schemas.ItemVariantCreate
) -> models.ItemVariant:
    db_item_variant = models.ItemVariant(**item_variant.model_dump())
    db.add(db_item_variant)
    db.commit()
    db.refresh(db_item_variant)
    return db_item_variant


def get_item_variant(db: Session, item_variant_id: str) -> models.ItemVariant | None:
    return (
        db.query(models.ItemVariant)
        .filter(models.ItemVariant.id == item_variant_id)
        .first()
    )


def update_item_variant(
    db: Session, item_variant_id: str, variant_update: schemas.ItemVariantCreate
) -> models.ItemVariant | None:
    """Update an item variant's details (excluding ID)."""
    db_variant = get_item_variant(db, item_variant_id)
    if not db_variant:
        return None

    db_variant.name = variant_update.name
    db_variant.volume = variant_update.volume

    db.commit()
    db.refresh(db_variant)
    return db_variant


def create_pickup_point(
    db: Session, pickup_point: schemas.PickupPointCreate
) -> models.PickupPoint:
    db_pickup_point = models.PickupPoint(**pickup_point.model_dump())
    db.add(db_pickup_point)
    db.commit()
    db.refresh(db_pickup_point)
    return db_pickup_point


def get_pickup_point(db: Session, pickup_point_id: str) -> models.PickupPoint | None:
    return (
        db.query(models.PickupPoint)
        .filter(models.PickupPoint.id == pickup_point_id)
        .first()
    )


def update_pickup_point(
    db: Session, pickup_point_id: str, point_update: schemas.PickupPointCreate
) -> models.PickupPoint | None:
    """Update a pickup point's details (excluding ID)."""
    db_point = get_pickup_point(db, pickup_point_id)
    if not db_point:
        return None

    db_point.name = point_update.name
    db_point.location = point_update.location

    db.commit()
    db.refresh(db_point)
    return db_point


def get_active_pickup_requests(
    db: Session
) -> List[schemas.PickupRequest]:
    return (
        db.query(models.PickupRequest)
    )


def create_pickup_request(
    db: Session, pickup_request: schemas.PickupRequest
) -> models.StoragePoint:
    db_pickup_request = models.PickupRequest(**pickup_request.model_dump())
    db.add(db_pickup_request)
    db.commit()
    db.refresh(db_pickup_request)
    return db_pickup_request


def delete_pickup_request(
    db: Session, id: str
) -> None:
    # TODO Alex
    return False


def get_pickup_request_responses(
    db: Session, id: str
) -> List[models.PickupRequestResponses]:
    return (
        db.query(models.PickupRequestResponses)
    )


def create_pickup_request_response(
    db: Session, id: str, current_user_id: any, resp: int, location: str = None
) -> bool:
    """Create a pickup request response with optional GPS location."""
    try:
        db_response = models.PickupRequestResponses(
            requestID=id,
            userID=current_user_id,
            result=resp,
            location=location
        )
        db.add(db_response)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def create_storage_point(
    db: Session, storage_point: schemas.StoragePointCreate
) -> models.StoragePoint:
    db_storage_point = models.StoragePoint(**storage_point.model_dump())
    db.add(db_storage_point)
    db.commit()
    db.refresh(db_storage_point)
    return db_storage_point


def get_storage_point(
    db: Session, storage_point_id: str
) -> models.StoragePoint | None:
    return (
        db.query(models.StoragePoint)
        .filter(models.StoragePoint.id == storage_point_id)
        .first()
    )


def update_storage_point(
    db: Session, storage_point_id: str, point_update: schemas.StoragePointCreate
) -> models.StoragePoint | None:
    """Update a storage point's details (excluding ID)."""
    db_point = get_storage_point(db, storage_point_id)
    if not db_point:
        return None

    db_point.name = point_update.name
    db_point.maxVolume = point_update.maxVolume
    db_point.location = point_update.location

    db.commit()
    db.refresh(db_point)
    return db_point


def create_drop_off_point(
    db: Session, drop_off_point: schemas.DropOffPointCreate
) -> models.DropOffPoint:
    db_drop_off_point = models.DropOffPoint(**drop_off_point.model_dump())
    db.add(db_drop_off_point)
    db.commit()
    db.refresh(db_drop_off_point)
    return db_drop_off_point


def get_drop_off_point(
    db: Session, drop_off_point_id: str
) -> models.DropOffPoint | None:
    return (
        db.query(models.DropOffPoint)
        .filter(models.DropOffPoint.id == drop_off_point_id)
        .first()
    )


def update_drop_off_point(
    db: Session, drop_off_point_id: str, point_update: schemas.DropOffPointCreate
) -> models.DropOffPoint | None:
    """Update a drop-off point's details (excluding ID)."""
    db_point = get_drop_off_point(db, drop_off_point_id)
    if not db_point:
        return None

    db_point.name = point_update.name
    db_point.location = point_update.location

    db.commit()
    db.refresh(db_point)
    return db_point


def create_items_at_pickup_point(
    db: Session, record: schemas.ItemsAtPickupPointCreate
) -> models.ItemsAtPickupPoint:
    db_record = models.ItemsAtPickupPoint(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_items_at_pickup_point(
    db: Session, pickup_point_id: str, item_variant_id: str
) -> models.ItemsAtPickupPoint | None:
    return (
        db.query(models.ItemsAtPickupPoint)
        .filter(
            models.ItemsAtPickupPoint.pickupPointID == pickup_point_id,
            models.ItemsAtPickupPoint.itemVariantID == item_variant_id,
        )
        .first()
    )


def get_all_items_at_pickup_point(
    db: Session, pickup_point_id: str
) -> list[models.ItemsAtPickupPoint]:
    return (
        db.query(models.ItemsAtPickupPoint)
        .filter(models.ItemsAtPickupPoint.pickupPointID == pickup_point_id)
        .all()
    )


def update_items_at_pickup_point(
    db: Session,
    pickup_point_id: str,
    item_variant_id: str,
    quantity: int,
) -> models.ItemsAtPickupPoint | None:
    """Update the quantity of items at a pickup point."""
    db_record = get_items_at_pickup_point(db, pickup_point_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity

    db.commit()
    db.refresh(db_record)
    return db_record


def create_items_in_car(
    db: Session, record: schemas.ItemsInCarCreate
) -> models.ItemsInCar:
    db_record = models.ItemsInCar(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_items_in_car(
    db: Session, user_id: str, item_variant_id: str
) -> models.ItemsInCar | None:
    return (
        db.query(models.ItemsInCar)
        .filter(
            models.ItemsInCar.userID == user_id,
            models.ItemsInCar.itemVariantID == item_variant_id,
        )
        .first()
    )


def get_all_items_in_car(
    db: Session, user_id: str
) -> list[models.ItemsInCar]:
    return (
        db.query(models.ItemsInCar)
        .filter(models.ItemsInCar.userID == user_id)
        .all()
    )


def update_items_in_car(
    db: Session,
    user_id: str,
    item_variant_id: str,
    quantity: int,
) -> models.ItemsInCar | None:
    """Update the quantity of items in a user's car."""
    db_record = get_items_in_car(db, user_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity

    db.commit()
    db.refresh(db_record)
    return db_record


def create_items_in_storage(
    db: Session, record: schemas.ItemsInStorageCreate
) -> models.ItemsInStorage:
    db_record = models.ItemsInStorage(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_items_in_storage(
    db: Session, storage_id: str, item_variant_id: str
) -> models.ItemsInStorage | None:
    return (
        db.query(models.ItemsInStorage)
        .filter(
            models.ItemsInStorage.storageID == storage_id,
            models.ItemsInStorage.itemVariantID == item_variant_id,
        )
        .first()
    )


def update_items_in_storage(
    db: Session,
    storage_id: str,
    item_variant_id: str,
    quantity: int,
) -> models.ItemsInStorage | None:
    """Update the quantity of items in storage."""
    db_record = get_items_in_storage(db, storage_id, item_variant_id)
    if not db_record:
        return None

    db_record.quantity = quantity

    db.commit()
    db.refresh(db_record)
    return db_record
