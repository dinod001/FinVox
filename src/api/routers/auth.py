import asyncio
import time
import os
import jwt
import bcrypt
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from src.infrastructure.db.crm_client import engine
from src.api.schemas import UserRegisterRequest, UserLoginRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
# JWT configuration
# In production, this should be loaded from .env (os.getenv("JWT_SECRET_KEY"))
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super_secret_finvox_key_change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days expiry

# ── Helpers ─────────────────────────────────────────────────────────

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password):
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": int(time.time()) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ── Endpoints ───────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(req: UserRegisterRequest):
    """Register a new user and return an access token."""
    hashed_password = get_password_hash(req.password)
    
    def _insert_user():
        with engine.begin() as conn:
            # Check if username or email already exists
            check_sql = "SELECT username FROM users WHERE username = :u OR email = :e"
            existing = conn.execute(text(check_sql), {"u": req.username, "e": req.email}).fetchone()
            if existing:
                return None
                
            # Insert new user
            insert_sql = """
                INSERT INTO users (username, email, password_hash)
                VALUES (:u, :e, :p)
                RETURNING username;
            """
            result = conn.execute(text(insert_sql), {
                "u": req.username,
                "e": req.email,
                "p": hashed_password
            })
            return result.fetchone()

    row = await asyncio.to_thread(_insert_user)
    if not row:
        raise HTTPException(status_code=400, detail="Username or email already registered")
        
    access_token = create_access_token(data={"sub": req.username})
    return AuthResponse(access_token=access_token, token_type="bearer", user_id=req.username)


@router.post("/login", response_model=AuthResponse)
async def login(req: UserLoginRequest):
    """Authenticate a user and return an access token."""
    def _verify_user():
        with engine.connect() as conn:
            # Check for matching username or email
            sql = "SELECT username, password_hash FROM users WHERE username = :u OR email = :u"
            return conn.execute(text(sql), {"u": req.username}).fetchone()
            
    user_row = await asyncio.to_thread(_verify_user)
    
    if not user_row or not verify_password(req.password, user_row.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
        
    access_token = create_access_token(data={"sub": user_row.username})
    return AuthResponse(access_token=access_token, token_type="bearer", user_id=user_row.username)
