from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .config import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    karma: Mapped[int] = mapped_column(Integer, nullable=False)
    maxVolume: Mapped[float] = mapped_column(Float, nullable=False)
    userType: Mapped[int] = mapped_column(Integer, nullable=False)


class ApiKey(Base):
    __tablename__ = "apiKeys"

    userID: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    keyHash: Mapped[str] = mapped_column(String, primary_key=True)


class ItemVariant(Base):
    __tablename__ = "itemVariants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)


class PickupPoint(Base):
    __tablename__ = "pickupPoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)


class StoragePoint(Base):
    __tablename__ = "storagePoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    maxVolume: Mapped[float] = mapped_column(Float, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)


class DropOffPoint(Base):
    __tablename__ = "dropOffPoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)


class ItemsAtPickupPoint(Base):
    __tablename__ = "itemsAtPickupPoint"

    pickupPointID: Mapped[str] = mapped_column(
        ForeignKey("pickupPoints.id"), primary_key=True
    )
    itemVariantID: Mapped[str] = mapped_column(
        ForeignKey("itemVariants.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class ItemsInCar(Base):
    __tablename__ = "itemsInCar"

    userID: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    itemVariantID: Mapped[str] = mapped_column(
        ForeignKey("itemVariants.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class ItemsInStorage(Base):
    __tablename__ = "itemsInStorage"

    storageID: Mapped[str] = mapped_column(
        ForeignKey("storagePoints.id"), primary_key=True
    )
    itemVariantID: Mapped[str] = mapped_column(
        ForeignKey("itemVariants.id"), primary_key=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
