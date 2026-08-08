"""
API routes for generating LiveKit Access Tokens so the Frontend can connect.
"""
import os
import uuid
from datetime import timedelta
from fastapi import APIRouter, HTTPException
from livekit.api import AccessToken, VideoGrants
from pydantic import BaseModel
from loguru import logger

router = APIRouter(prefix="/voice", tags=["Voice Agent"])

class TokenRequest(BaseModel):
    user_id: str | None = None
    room_name: str | None = None

@router.post("/token")
async def generate_token(req: TokenRequest):
    """
    Generate a LiveKit access token for a user to join the Voice AI room.
    """
    user_id = req.user_id or f"user_{str(uuid.uuid4())[:8]}"
    room_name = req.room_name or str(uuid.uuid4())

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not api_key or not api_secret:
        logger.error("LIVEKIT_API_KEY or LIVEKIT_API_SECRET not found in environment variables.")
        raise HTTPException(status_code=500, detail="LiveKit credentials are not configured on the server.")

    # Create the token
    token = AccessToken(api_key, api_secret)
    token.with_identity(user_id)
    token.with_name(user_id)
    
    # Give the user permission to join the specific room and talk
    grant = VideoGrants(
        room_join=True, 
        room=room_name, 
        can_publish=True, 
        can_subscribe=True
    )
    token.with_grants(grant)
    
    # Token valid for 2 hours
    token.with_ttl(timedelta(hours=2))

    jwt_token = token.to_jwt()
    logger.info(f"Generated LiveKit token for {user_id} in room {room_name}")

    return {
        "access_token": jwt_token,
        "url": livekit_url,
        "user_id": user_id,
        "room_name": room_name
    }
