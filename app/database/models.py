from sqlalchemy import String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .config import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    karma: Mapped[int] = mapped_column(Integer, nullable=False)
    maxVolume: Mapped[int] = mapped_column(Integer, nullable=False)
    userType: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)


class ApiKey(Base):
    __tablename__ = "apiKeys"

    userID: Mapped[str] = mapped_column(
        ForeignKey("users.id"), primary_key=True)
    keyHash: Mapped[str] = mapped_column(String, primary_key=True)


class ItemVariant(Base):
    __tablename__ = "itemVariants"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    volume: Mapped[int] = mapped_column(Integer, nullable=False)


class PickupPoint(Base):
    __tablename__ = "pickupPoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)


class PickupRequest(Base):
    __tablename__ = "pickupRequests"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pickupPointID: Mapped[str] = mapped_column(
        ForeignKey("pickupPoints.id"), nullable=False)


class PickupRequestResponses(Base):
    __tablename__ = "pickupRequestResponses"

    requestID: Mapped[str] = mapped_column(
        ForeignKey("pickupRequests.id"), primary_key=True)
    userID: Mapped[str] = mapped_column(
        ForeignKey("users.id"), primary_key=True)
    result: Mapped[int] = mapped_column(Integer, nullable=False)


class StoragePoint(Base):
    __tablename__ = "storagePoints"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    maxVolume: Mapped[int] = mapped_column(Integer, nullable=False)
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

    userID: Mapped[str] = mapped_column(
        ForeignKey("users.id"), primary_key=True)
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


class Auction(Base):
    """Tracks an active auction for a pickup request.
    
    Auction remains active until manager manually triggers processing.
    """
    __tablename__ = "auctions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    pickupRequestID: Mapped[str] = mapped_column(
        ForeignKey("pickupRequests.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")  # active, closed, completed
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    winnerUserID: Mapped[str] = mapped_column(
        ForeignKey("users.id"), nullable=True)


class AuctionBid(Base):
    """Tracks volunteer bids/responses to an auction."""
    __tablename__ = "auctionBids"

    auctionID: Mapped[str] = mapped_column(
        ForeignKey("auctions.id"), primary_key=True)
    userID: Mapped[str] = mapped_column(
        ForeignKey("users.id"), primary_key=True)
    accepted: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = yes, 0 = no
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    estimatedTime: Mapped[float] = mapped_column(Float, nullable=True)  # Minutes to pickup
    score: Mapped[float] = mapped_column(Float, nullable=True)  # Final calculated score
    createdAt: Mapped[datetime] = mapped_column(DateTime, nullable=False)
