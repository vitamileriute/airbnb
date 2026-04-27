from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import os
import re
import pyairbnb

app = FastAPI()

TOKEN = os.getenv("SERVICE_TOKEN")  # optional shared secret


class PriceReq(BaseModel):
    url: Optional[str] = None
    room_id: Optional[str] = None
    check_in: str        # "YYYY-MM-DD"
    check_out: str       # "YYYY-MM-DD"
    adults: int = 1
    currency: str = "USD"


def auth(authorization: Optional[str]):
    if TOKEN and authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


def extract_id(url: Optional[str]):
    match = re.search(r"/rooms/(\d+)", url or "")
    return match.group(1) if match else None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/details")
def details(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)

    room_id = body.room_id or extract_id(body.url)

    if not room_id:
        return {"ok": False, "error": "room_id or valid url required"}

    try:
        data = pyairbnb.get_details(
            room_id=str(room_id),
            currency=body.currency,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
            proxy_url="",
        )

        if isinstance(data, tuple):
            data = data[0]

        return {"ok": True, "data": data}

    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/price")
def price(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)

    room_id = body.room_id or extract_id(body.url)

    if not room_id:
        return {"ok": False, "error": "room_id or valid url required"}

    try:
        details_data, price_input, cookies = pyairbnb.get_details(
            room_id=str(room_id),
            currency=body.currency,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
            proxy_url="",
        )

        api_key = price_input["api_key"]
        product_id = price_input["product_id"]
        impression_id = price_input.get("impression_id", "")

        price_data = pyairbnb.get_price(
            product_id=product_id,
            api_key=api_key,
            cookies=cookies,
            impression_id=impression_id,
            currency=body.currency,
            check_in=body.check_in,
            check_out=body.check_out,
            adults=body.adults,
            proxy_url="",
        )

        return {"ok": True, "data": price_data}

    except Exception as e:
        return {"ok": False, "error": str(e)}
