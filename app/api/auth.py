from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from fastapi_users.jwt import generate_jwt
from fastapi_users.password import PasswordHelper
from fastapi_users.exceptions import UserNotExists, UserAlreadyExists
from pydantic import EmailStr, ValidationError, parse_obj_as
from sqlalchemy import select
from app.deps.users import get_user_manager, get_jwt_strategy, UserManager
from app.models.user import User as UserModel
from app.schemas.user import UserCreate
from app.deps.db import CurrentAsyncSession
import random
from datetime import datetime, timezone
from app.services.mail import send_otp_email

password_helper = PasswordHelper()

router = APIRouter()

@router.post(
    "/auth/jwt/login",
    summary="Authenticates a user with email and password.",
)
async def custom_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager)
):
    try:
        user: UserModel = await user_manager.get_by_email(form_data.username)
    except UserNotExists:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email and password you entered don't match",
        )

    verified, updated_password_hash = password_helper.verify_and_update(
        form_data.password, user.hashed_password
    )

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The email and password you entered don't match",
        )

    if updated_password_hash is not None:
        await user_manager.update(
            user, update_dict={"hashed_password": updated_password_hash}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive account",
        )
        
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unverified account",
        )

    jwt_strategy = get_jwt_strategy()
    token = generate_jwt(
        {"sub": str(user.id), "aud": ["fastapi-users:auth"]},
        jwt_strategy.secret,
        lifetime_seconds=jwt_strategy.lifetime_seconds
    )

    return JSONResponse({"access_token": token, "token_type": "bearer"})


@router.post(
    "/auth/register",
    summary="Create a new user account with email and password.",
)
async def custom_register(
    session: CurrentAsyncSession,
    user_data: dict = Body(...),
    user_manager: UserManager = Depends(get_user_manager),
):
    email = user_data.get("email")

    try:
        parse_obj_as(EmailStr, email)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email entered is not a valid email address: Email address must contain the @ sign.",
        )
        
    existing_user = await session.scalar(select(UserModel).where(UserModel.email == email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email already exists.",
        )
        
    phone_e164 = user_data.get("phone_e164")
    if phone_e164:
        phone_exists = await session.scalar(select(UserModel).where(UserModel.phone_e164 == phone_e164))
        if phone_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The phone number already exists.",
            )
            
    try:
        created_user = await user_manager.create(
            UserCreate(**user_data)
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The email already exists",
        )
        
    otp_code = str(random.randint(100000, 999999))
    try:
        send_otp_email(created_user.email, otp_code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}",
        )
        
    created_user.otp_code = otp_code
    await session.commit()

    return {
        "id": str(created_user.id),
        "email": created_user.email
    }


@router.post("/auth/verify-otp")
async def verify_otp(session: CurrentAsyncSession, email: str = Body(...), otp_code: str = Body(...)):
    user = await session.scalar(select(UserModel).where(UserModel.email == email))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.otp_code != otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    user.otp_code = None
    await session.commit()

    return {"message": "Email verified successfully"}
