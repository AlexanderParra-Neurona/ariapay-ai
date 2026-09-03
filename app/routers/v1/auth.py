from fastapi import APIRouter, HTTPException

from app.constants import HTTP_STATUS_BAD_GATEWAY, HTTP_STATUS_UNAUTHORIZED
from app.schemas import LoginRequest, LoginResponse
from app.services.ariapay_service import (
    AriapayAPIError,
    AriapayAuthError,
    login,
    verify_passcode,
)

router = APIRouter(prefix="/auth")


@router.post("/login", response_model=LoginResponse)
async def auth_login(req: LoginRequest):
    try:
        passcode_token = await login(req.phone_number, req.country_code, req.password)
        token = await verify_passcode(passcode_token, req.passcode)
    except AriapayAuthError as e:
        raise HTTPException(status_code=HTTP_STATUS_UNAUTHORIZED, detail=str(e))
    except AriapayAPIError as e:
        raise HTTPException(status_code=HTTP_STATUS_BAD_GATEWAY, detail=str(e))
    return LoginResponse(
        access_token=token["access_token"], refresh_token=token["refresh_token"]
    )
