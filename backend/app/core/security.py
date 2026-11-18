import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from app.core.config import settings


def get_password_hash(password: str) -> str:
    """Hash a plain text password using bcrypt."""
    # bcrypt requires bytes, so we encode the string to UTF-8
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a plain password matches the hashed password in the DB."""
    pwd_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except ValueError:
        # If the hash in the DB is somehow malformed, return False safely
        return False


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Create a JWT access token. 'subject' is usually the User ID."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Fall back to the default from .env (60 minutes)
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # The token payload contains the expiration time and the subject (User ID)
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Encode the token using our secret key from .env
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """Decode a JWT token. Returns None if the token is invalid or expired."""
    try:
        decoded_token = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded_token
    except jwt.PyJWTError:
        return None