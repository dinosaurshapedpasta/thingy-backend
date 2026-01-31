import hashlib
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database import get_db, crud


def hash_api_key(api_key: str) -> str:
    """Hash an API key using SHA256."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_current_user(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Dependency that validates the API key and returns the current user.

    - Hashes the incoming X-API-Key
    - Looks it up in the apiKeys table
    - Returns the associated user
    - Raises 401 if invalid
    """
    key_hash = hash_api_key(x_api_key)

    # Find the API key in the database
    api_key_record = db.query(crud.models.ApiKey).filter(
        crud.models.ApiKey.keyHash == key_hash
    ).first()

    if not api_key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Get the user associated with this API key
    user = crud.get_user(db, api_key_record.userID)

    if not user:
        raise HTTPException(status_code=401, detail="User not found for this API key")

    return user
