from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import os
import pyairbnb

app = FastAPI()
TOKEN = os.getenv("SERVICE_TOKEN")  # optional shared secret

class PriceReq(BaseModel):
    url: str
    check_in: str        # "YYYY-MM-DD"
    check_out: str
    adults: int = 1
    currency: str = "USD"

def auth(authorization: Optional[str]):
    if TOKEN and authorization != f"Bearer {TOKEN}":
        raise HTTPException(401, "unauthorized")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/details")
def details(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)
    try:
        data = pyairbnb.get_details(
            room_url=body.url,
            currency=body.currency,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
        )
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/price")
def price(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)
    try:
        data = pyairbnb.get_price(
            room_url=body.url,
            currency=body.currency,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
        )
        return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}
