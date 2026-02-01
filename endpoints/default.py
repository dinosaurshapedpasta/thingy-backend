from fastapi import APIRouter

router = APIRouter(tags=["default"])


@router.get("/test")
def test_endpoint():
    """Check the API is online."""
    return {"message": "API online ✅"}
