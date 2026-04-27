from datetime import date
from typing import Optional

import pyairbnb
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SERVICE_TOKEN = ""  # optional: put your token here if you use one


class DetailsReq(BaseModel):
    url: str
    check_in: Optional[str] = ""
    check_out: Optional[str] = ""
    adults: Optional[int] = 1
    currency: Optional[str] = "USD"


class PriceReq(BaseModel):
    room_id: Optional[str] = None
    url: Optional[str] = None
    check_in: str
    check_out: str
    adults: Optional[int] = 1
    currency: Optional[str] = "USD"


def auth(authorization: Optional[str]):
    if SERVICE_TOKEN:
        expected = f"Bearer {SERVICE_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")


def extract_id(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    import re

    match = re.search(r"/rooms/(?:plus/)?(\d+)", url)
    return match.group(1) if match else None


@app.get("/")
def root():
    return {"ok": True, "service": "pyairbnb"}


@app.post("/details")
def details(body: DetailsReq, authorization: Optional[str] = Header(None)):
    auth(authorization)

    try:
        room_id = extract_id(body.url)
        if not room_id:
            raise Exception("Could not extract room_id from URL")

        result = pyairbnb.get_details(
            room_id=str(room_id),
            currency=body.currency or "USD",
        )

        return {"ok": True, "data": result}

    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/price")
def price(body: PriceReq, authorization: Optional[str] = Header(None)):
    auth(authorization)

    try:
        room_id = body.room_id or extract_id(body.url)
        if not room_id:
            raise Exception("room_id or valid Airbnb url is required")

        result = pyairbnb.get_price(
            room_id=str(room_id),
            check_in=date.fromisoformat(body.check_in),
            check_out=date.fromisoformat(body.check_out),
            adults=int(body.adults or 1),
            currency=body.currency or "USD",
            api_key=None,
            cookies=None,
            impression_id=None,
            proxy_url="",
        )

        return {"ok": True, "data": result}

    except Exception as e:
        return {"ok": False, "error": str(e)}
