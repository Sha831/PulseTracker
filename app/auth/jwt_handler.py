from jose import jwt, ExpiredSignatureError
from datetime import datetime, timedelta, timezone

SECRET_KEY = "my_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=15)


def _create_jwt_payload(org_id:str) -> dict:
    current_time = datetime.now(timezone.utc)
    payload = {'sub': org_id , 
               'exp': current_time+ACCESS_TOKEN_EXPIRE_MINUTES, 
               'iat': current_time,
               'iss': 'Pulsetrack'
               }
    return payload


def create_token(org_id: str) -> str:
    payload = _create_jwt_payload(org_id)
    token = jwt.encode(payload,SECRET_KEY,ALGORITHM)
    return token


def verify_token(token:str) -> dict:
    payload = jwt.decode(token=token,key=SECRET_KEY,algorithms=[ALGORITHM])
    return(payload)



def main():
    print(verify_token('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdfaWQiOiJhbXpfMTAxIiwiZXhwIjoxNzgyODA0OTgyfQ.xwARgLWcHTva_rjJvhANiGydDlS-zhfQ3nYv785ErOE'))

if __name__ == "__main__":
    main()