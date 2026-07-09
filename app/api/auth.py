from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.sessions import get_db_session
from app.auth.services import authenticate_organization
from app.schemas.auth import TokenRequest, TokenResponse

"""
Authentication API Endpoints

Responsibilities:
- accept org credeantials
- delegate authentication to service layer
- issues JWT access tokens
"""

router = APIRouter()

@router.post("/auth/token",status_code=status.HTTP_202_ACCEPTED,response_model=TokenResponse)
def issue_token(
    claims : TokenRequest,
    session: Session = Depends(get_db_session),
):
    """
    authenticates org using its API key and returns signed JWT access token
    the endpoint handles http request and repomse serialization , it delegates all authentication logic to service layer
    """
    token = authenticate_organization(claims.organization_id,session,claims.api_key)

    return TokenResponse(token=token)