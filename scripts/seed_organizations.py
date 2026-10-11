from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker,Session
import uuid

"""
Disclamer : 
-Please dont refer these test scripts for general testing as these were made during specific cases/time during designing backend
"""
# since we dont have any api's to register an organization for now
# Test script to manually add organization details to database 
DATABASE_URL = "postgres____xyz___5432/pulsetrack"   # add the db url to actual db

engine = create_engine(
    DATABASE_URL,
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


def generate_organization_data(org_name:str) -> dict:

    return {
    "org_name": org_name,
    "organization_id": uuid.uuid4(),
    "api_key": f"__hghjgbvhv__",#add your secret key 
        }


def add_org_to_db(org_name:str,session:Session):
    insert_into_organizations = text("""
    INSERT INTO organizations (
    organization_id,
    organization_name,
    api_key,
    is_active
    )VALUES (
        :organization_id,
        :organization_name,
        :api_key,
        :is_active
    );
    """)

    org_info = generate_organization_data(org_name)

    session.execute(
        insert_into_organizations,
        {
            "organization_id":org_info['organization_id'],
            "organization_name":org_info['org_name'],
            "api_key":org_info['api_key'],
            "is_active":True,
        }
    )


def main(org_list:list,session:Session):
    for org in org_list:
        add_org_to_db(org,session)

if __name__ == "__main__":
    session = SessionLocal()
    try:
        org_list = ["amazon", "flipkart", "google", "tesla", "openai"]
        main(org_list, session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()