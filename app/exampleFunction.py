from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.get("/example")
async def fun(req: Request):
    body = await req.json()
    if "val1" not in body:
        raise HTTPException(400, "Missing text")
    val1 = body["val1"]
    
    # do something

    return {"val1": val1}