from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

from app.auth.jwt_handler import verify_token
from app.schemas.auth import JWTPayload
"""
Authentication Dependencies

Responsibilities:
- extracts JWT from http request header 
"""

bearer_scheme = HTTPBearer()

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> JWTPayload:

    token = credentials.credentials

    token_payload = verify_token(token=token)

    return token_payload