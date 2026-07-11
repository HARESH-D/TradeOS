from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(AuthRequest):
    name: str = Field(min_length=2, max_length=120)


class BrokerConnectRequest(BaseModel):
    mode: Literal["demo", "angel"] = "demo"
    api_key: str | None = None
    client_code: str | None = None
    pin: str | None = None
    totp: str | None = None

