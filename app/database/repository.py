from typing import TypeVar, Generic, Type, Optional, Dict, Any
from sqlalchemy.orm import Session, DeclarativeBase
from pydantic import BaseModel

from . import models

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic repository for CRUD operations.

    Eliminates code duplication by providing common patterns for:
    - Create: db.add() + commit + refresh
    - Get by ID: query + filter + first
    - Update: field assignment + commit + refresh
    - List/Query: query + filter + all
    """

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, obj_in: CreateSchemaType) -> ModelType:
        """Generic create - works for all simple models."""
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, id: str) -> Optional[ModelType]:
        """Generic get by single ID field."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_composite_key(
        self, db: Session, filters: Dict[str, Any]
    ) -> Optional[ModelType]:
        """Generic get by composite key (for junction tables)."""
        query = db.query(self.model)
        for field, value in filters.items():
            query = query.filter(getattr(self.model, field) == value)
        return query.first()

    def update(
        self, db: Session, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        """
        Generic update using model_dump(exclude_unset=True).
        Only updates fields provided in the request.
        """
        update_data = obj_in.model_dump(exclude_unset=True, exclude={'id'})
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def list_all(self, db: Session, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """Generic list with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def filter_by(
        self, db: Session, filters: Dict[str, Any], skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Generic filter by multiple conditions."""
        query = db.query(self.model)
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query.offset(skip).limit(limit).all()


# Concrete repository instances for each model
class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.User)


class ApiKeyRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.ApiKey)

    def get_by_keys(
        self, db: Session, user_id: str, key_hash: str
    ) -> Optional[models.ApiKey]:
        """Get API key by composite key."""
        return self.get_by_composite_key(
            db, {"userID": user_id, "keyHash": key_hash}
        )


class ItemVariantRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.ItemVariant)


class PickupPointRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.PickupPoint)


class PickupRequestRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.PickupRequest)


class PickupRequestResponsesRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.PickupRequestResponses)

    def get_by_keys(
        self, db: Session, request_id: str, user_id: str
    ) -> Optional[models.PickupRequestResponses]:
        """Get response by composite key."""
        return self.get_by_composite_key(
            db, {"requestID": request_id, "userID": user_id}
        )


class StoragePointRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.StoragePoint)


class DropOffPointRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.DropOffPoint)


class ItemsAtPickupPointRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.ItemsAtPickupPoint)

    def get_by_keys(
        self, db: Session, pickup_point_id: str, item_variant_id: str
    ) -> Optional[models.ItemsAtPickupPoint]:
        """Get items at pickup by composite key."""
        return self.get_by_composite_key(
            db, {"pickupPointID": pickup_point_id, "itemVariantID": item_variant_id}
        )


class ItemsInCarRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.ItemsInCar)

    def get_by_keys(
        self, db: Session, user_id: str, item_variant_id: str
    ) -> Optional[models.ItemsInCar]:
        """Get items in car by composite key."""
        return self.get_by_composite_key(
            db, {"userID": user_id, "itemVariantID": item_variant_id}
        )


class ItemsInStorageRepository(BaseRepository):
    def __init__(self):
        super().__init__(models.ItemsInStorage)

    def get_by_keys(
        self, db: Session, storage_id: str, item_variant_id: str
    ) -> Optional[models.ItemsInStorage]:
        """Get items in storage by composite key."""
        return self.get_by_composite_key(
            db, {"storageID": storage_id, "itemVariantID": item_variant_id}
        )


# Initialize repository singletons
user_repo = UserRepository()
api_key_repo = ApiKeyRepository()
item_variant_repo = ItemVariantRepository()
pickup_point_repo = PickupPointRepository()
pickup_request_repo = PickupRequestRepository()
pickup_request_responses_repo = PickupRequestResponsesRepository()
storage_point_repo = StoragePointRepository()
dropoff_point_repo = DropOffPointRepository()
items_at_pickup_repo = ItemsAtPickupPointRepository()
items_in_car_repo = ItemsInCarRepository()
items_in_storage_repo = ItemsInStorageRepository()
