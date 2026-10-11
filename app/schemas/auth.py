from pydantic import BaseModel, StringConstraints
from uuid import UUID
from typing import Literal, Annotated


class TokenRequest(BaseModel):
    organization_id : UUID
    api_key : Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TokenResponse(BaseModel):
    token : str


class JWTPayload(BaseModel):
    sub: UUID
    exp: int 
    iat: int
    iss: Literal['Pulsetrack']