from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import date
import os
import re
import pyairbnb

app = FastAPI()

TOKEN = os.getenv("SERVICE_TOKEN")


class PriceReq(BaseModel):
    url: Optional[str] = None
    room_id: Optional[str] = None
    check_in: str
    check_out: str
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
        room_url = f"https://www.airbnb.com/rooms/{room_id}"

        details_data, price_input, cookies = pyairbnb.get_metadata_from_url(
            room_url,
            "en",
            "",
        )

        return {
            "ok": True,
            "data": details_data,
            "price_input": price_input,
        }

    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/price")
def price(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)

    room_id = body.room_id or extract_id(body.url)

    if not room_id:
        return {"ok": False, "error": "room_id or valid url required"}

    try:
        room_url = f"https://www.airbnb.com/rooms/{room_id}"

        data, price_input, cookies = pyairbnb.get_metadata_from_url(
            room_url,
            "en",
            "",
        )

        price_data = pyairbnb.get_price(
            price_input["api_key"],
            cookies,
            price_input["impression_id"],
            price_input["product_id"],
            date.fromisoformat(body.check_in),
            date.fromisoformat(body.check_out),
            body.adults,
            body.currency,
            "",
        )

        return {"ok": True, "data": price_data}

    except Exception as e:
        return {"ok": False, "error": str(e)}
