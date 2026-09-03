from pydantic import BaseModel


class LoginRequest(BaseModel):
    phone_number: str
    country_code: str
    password: str
    passcode: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
