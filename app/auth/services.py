from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from uuid import UUID

from app.auth.jwt_handler import create_token
"""
Authentication Service

Responsibilities:
- Authenticates an org using org_id and api_key
- verifies the provided org crediantials
- Return a valid JWT acces token
"""

def get_organization_info(org_id:UUID, session:Session) -> dict:

    get_org_status = text("""SELECT api_key,is_active 
                          FROM organizations 
                          WHERE organization_id = :org_id""")

    try:
        result = session.execute(get_org_status,{"org_id":org_id}).mappings().one()

    except NoResultFound as e:
        raise HTTPException(status_code=401)
    
    return dict(result)


def verify_api_key(claimed_api_key: str, actual_api_key: str):
    ### for now just equate the api_key string , later will store hash instead of key for extra security 
    return claimed_api_key == actual_api_key


def authenticate_organization(org_id:UUID,session:Session,claimed_api_key:str) -> str:

    organization_info = get_organization_info(org_id,session=session)

    is_valid_api_key = verify_api_key(claimed_api_key,organization_info["api_key"])

    if organization_info["is_active"] and is_valid_api_key:
        return create_token(org_id)
    
    else:
        e = "organization status inactive or incorrect api_key"
        raise HTTPException(status_code=401, detail=str(e))