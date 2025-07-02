from datetime import datetime, timedelta
import pytz
from typing import Any, Union, Optional
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
import bcrypt
import secrets

from app.core.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
timezone_name = "Africa/Lagos"
tz = pytz.timezone(timezone_name)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.now(tz) + expires_delta
    else:
        expire = datetime.now(tz) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""


    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """Generate password hash"""

    salt= bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')
    bt = bcrypt.hashpw(pwd_bytes, salt)
    return bt.decode("utf-8")

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return subject"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        token_data = payload.get("sub")

        print("subby", token_data)
        return token_data
    
    except ExpiredSignatureError:
        print("expiredddd", )
        return None
    except JWTError:
        
        return None
    