from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
from datetime import datetime, timedelta,timezone
from uuid import UUID
from fastapi.exceptions import HTTPException
import os

from app.schemas.auth import JWTPayload
from app.core.config import SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
"""
JWT 

Responsibilities:
- Creates JWT access tokens
- verify JWT and return a trusted payload
"""

def _create_jwt_payload(org_id:UUID) -> dict:
    current_time = datetime.now(timezone.utc)
    payload = {'sub': str(org_id),
               'exp': current_time+timedelta(minutes=JWT_EXPIRE_MINUTES), 
               'iat': current_time,
               'iss': 'Pulsetrack'
               }
    return payload


def create_token(org_id: UUID) -> str:
    payload = _create_jwt_payload(org_id)
    token = jwt.encode(payload,SECRET_KEY,JWT_ALGORITHM)
    return token


def verify_token(token:str) -> JWTPayload:
    try:
        raw_payload = jwt.decode(token=token,key=SECRET_KEY,algorithms=[JWT_ALGORITHM])
        # jwt.decode() only verifies signature and expiration time
        # verify the payload to ensure all required claims are present
        payload = JWTPayload.model_validate(raw_payload)
        return payload
        
    except ValidationError:
        raise HTTPException(status_code=401,detail=" Invalid or Expired Token ")

    except JWTError:
        raise HTTPException(status_code=401, detail=" Invalid or Expired Token ")