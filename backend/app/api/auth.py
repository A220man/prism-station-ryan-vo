from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from jose import jwt
import httpx
import secrets

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
    oidc_config,
    TokenData,
)
from app.models.skill import User
from app.services.skill_service import UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    roles: list[str]

    class Config:
        from_attributes = True


class OIDCLoginResponse(BaseModel):
    authorization_url: str
    state: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.create_user(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )
    return UserResponse.from_orm(user)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user_by_email(form_data.username)
    if not user or not service.verify_password(user, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "roles": user.roles},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user(int(current_user.sub))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/oidc/login", response_model=OIDCLoginResponse)
async def oidc_login():
    if not oidc_config.is_configured():
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not configured")

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    params = {
        "response_type": "code",
        "client_id": oidc_config.client_id,
        "redirect_uri": oidc_config.redirect_uri,
        "scope": "openid email profile",
        "state": state,
        "nonce": nonce,
    }

    auth_url = f"{oidc_config.issuer_url}/protocol/openid-connect/auth"
    from urllib.parse import urlencode
    authorization_url = f"{auth_url}?{urlencode(params)}"

    return OIDCLoginResponse(authorization_url=authorization_url, state=state)


@router.get("/oidc/callback")
async def oidc_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    if not oidc_config.is_configured():
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not configured")

    token_url = f"{oidc_config.issuer_url}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": oidc_config.redirect_uri,
        "client_id": oidc_config.client_id,
        "client_secret": oidc_config.client_secret,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=data)
        token_response.raise_for_status()
        tokens = token_response.json()

    access_token = tokens.get("access_token")
    id_token = tokens.get("id_token")

    if not access_token or not id_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token response")

    try:
        claims = jwt.decode(id_token, options={"verify_signature": False})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID token")

    oidc_sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")

    if not oidc_sub or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required claims")

    service = UserService(db)
    user = service.get_user_by_oidc_sub(oidc_sub)
    if not user:
        user = service.get_user_by_email(email)
        if user:
            user.oidc_sub = oidc_sub
            db.commit()
            db.refresh(user)
        else:
            user = service.create_user(email=email, password=secrets.token_urlsafe(32), full_name=name)
            user.oidc_sub = oidc_sub
            db.commit()
            db.refresh(user)

    app_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "roles": user.roles},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    frontend_url = settings.frontend_url
    return Response(
        content=f"""
        <html>
        <body>
        <script>
            window.opener.postMessage({{token: "{app_token}"}}, "{frontend_url}");
            window.close();
        </script>
        </body>
        </html>
        """,
        media_type="text/html",
    )


@router.get("/oidc/config")
async def oidc_config_endpoint():
    return {
        "enabled": oidc_config.enabled,
        "issuer_url": oidc_config.issuer_url,
        "client_id": oidc_config.client_id,
        "redirect_uri": oidc_config.redirect_uri,
    }