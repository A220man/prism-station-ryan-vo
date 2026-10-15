from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2AuthorizationCodeBearer
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)
oidc_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="", tokenUrl="", auto_error=False
)


class TokenData(BaseModel):
    sub: Optional[str] = None
    email: Optional[str] = None
    roles: list[str] = []
    exp: Optional[int] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # bcrypt has a 72-byte limit; truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenData(
            sub=payload.get("sub"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=payload.get("exp"),
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(token)


async def get_current_user_optional(token: str = Depends(oauth2_scheme)) -> Optional[TokenData]:
    if not token:
        return None
    try:
        return decode_token(token)
    except HTTPException:
        return None


def require_role(required_roles: list[str]):
    async def role_checker(user: TokenData = Depends(get_current_user)) -> TokenData:
        if not any(role in user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user
    return role_checker


class OIDCConfig:
    def __init__(self):
        self.enabled = settings.oidc_enabled
        self.issuer_url = settings.oidc_issuer_url
        self.client_id = settings.oidc_client_id
        self.client_secret = settings.oidc_client_secret
        self.redirect_uri = settings.oidc_redirect_uri
        self._jwks_cache: Optional[Dict] = None
        self._jwks_fetched_at: Optional[datetime] = None

    def is_configured(self) -> bool:
        return self.enabled and all([
            self.issuer_url,
            self.client_id,
            self.client_secret,
            self.redirect_uri,
        ])


oidc_config = OIDCConfig()