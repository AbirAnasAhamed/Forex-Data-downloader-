from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import redis.asyncio as redis
import logging

from backend.app.database.timescale_engine import get_db
from backend.app.database.redis_engine import get_redis_client
from backend.app.database.models.user import User
from backend.app.core.cryptography import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Dependency to get current user and check blacklisted tokens
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    # Check if token is blacklisted in Redis
    is_blacklisted = await redis_client.get(f"bl_{token}")
    if is_blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        
    return user

@router.post("/login")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    # Blacklist the token in Redis for its remaining lifetime
    # For simplicity, we just set a conservative expiry like 2 hours
    await redis_client.setex(f"bl_{token}", 7200, "true")
    return {"message": "Successfully logged out"}

# Developer endpoint to create initial admin user if none exists
@router.post("/setup")
async def create_initial_admin(db: Session = Depends(get_db)):
    existing = db.query(User).first()
    if existing:
        return {"message": "Admin already exists"}
    
    hashed_pw = get_password_hash("admin123")
    new_user = User(username="admin", hashed_password=hashed_pw, role="admin")
    db.add(new_user)
    db.commit()
    return {"message": "Admin created with username 'admin' and password 'admin123'"}
