import os
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

# Initialize Argon2 Password Hasher with Hedge Fund standard memory-hard settings
# time_cost: number of iterations
# memory_cost: memory usage in KiB (e.g., 65536 = 64MB)
# parallelism: number of threads
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against an Argon2 hash.
    """
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except Exception as e:
        logging.error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Generates an Argon2 hash for a given password.
    """
    return ph.hash(password)

def needs_rehash(hashed_password: str) -> bool:
    """
    Checks if a password needs to be rehashed due to parameter changes.
    """
    return ph.check_needs_rehash(hashed_password)

from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional

# Secret key for JWT (Should be stored in AWS KMS or strong .env in production)
# For now, using a strong fallback for development
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "b3c9b8f2d5e7a1f4c6e9d8b2a3f1c4e7d5b8a9f2c3e4d5b6a7f8e9d0c1b2a3f4")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

