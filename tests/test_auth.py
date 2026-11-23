from uuid import uuid4

import pytest
from sqlalchemy import text

from app.auth.jwt_handler import verify_token


def get_active_organization(db_session):
    return db_session.execute(
        text("""
            SELECT organization_id, api_key
            FROM organizations
            WHERE is_active = TRUE
            LIMIT 1
        """)
    ).mappings().one()


def test_auth_success(client, db_session):
    organization = get_active_organization(db_session)

    response = client.post(
        "/auth/token",
        json={
            "organization_id": str(organization["organization_id"]),
            "api_key": organization["api_key"]
        }
    )

    assert response.status_code == 202

    token = response.json()["token"]
    assert token

    # Verify that the issued JWT is valid and belongs to this organization.
    payload = verify_token(token)

    assert payload.sub == organization["organization_id"]


def test_auth_invalid_api_key(client, db_session):
    organization = get_active_organization(db_session)

    response = client.post(
        "/auth/token",
        json={
            "organization_id": str(organization["organization_id"]),
            "api_key": "invalid-api-key"
        }
    )

    assert response.status_code == 401


def test_auth_inactive_organization(client, db_session):
    organization = get_active_organization(db_session)
    org_id = organization["organization_id"]

    try:
        db_session.execute(
            text("""
                UPDATE organizations
                SET is_active = FALSE
                WHERE organization_id = :org_id
            """),
            {"org_id": org_id}
        )
        db_session.commit()

        response = client.post(
            "/auth/token",
            json={
                "organization_id": str(org_id),
                "api_key": organization["api_key"]
            }
        )

        assert response.status_code == 401

    finally:
        db_session.execute(
            text("""
                UPDATE organizations
                SET is_active = TRUE
                WHERE organization_id = :org_id
            """),
            {"org_id": org_id}
        )
        db_session.commit()


def test_auth_unknown_organization(client):
    response = client.post(
        "/auth/token",
        json={
            "organization_id": str(uuid4()),
            "api_key": "some-api-key"
        }
    )

    assert response.status_code == 401
