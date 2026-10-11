from sqlalchemy import create_engine, insert
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker,Session, DeclarativeBase, Mapped, mapped_column
from pydantic import BaseModel, Field, StringConstraints
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Annotated
from uuid import UUID, uuid4
import random
import string

"""
Disclamer : 
-Please dont refer these test scripts for general testing as these were made during specific cases/time during designing backend
"""

# since we have not written test script for ingestion api's
# Test script to manually add events to test analytic api's

DATABASE_URL = "postgres____xyz___5432/pulsetrack" #path to ur database

engine = create_engine(
    DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


class RawEvents(Base):
    __tablename__ = "raw_events"

    event_id : Mapped[UUID] = mapped_column(primary_key=True)
    organization_id: Mapped[UUID]
    event_type: Mapped[str]
    occurred_at: Mapped[datetime]
    received_at: Mapped[datetime]
    user_id: Mapped[Optional[str]]
    event_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata",JSONB)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    idempotency_key : Mapped[str] = mapped_column(primary_key=True)
    event_id : Mapped[UUID] 
    received_at : Mapped[datetime]



class SampleEvent(BaseModel):
    event_id: UUID
    event_type: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1)]
    occurred_at: datetime
    received_at:datetime
    user_id: Optional[str] = None
    organization_id: UUID
    event_metadata: Dict[str,Any] = Field(default_factory=dict)


class SampleIdempotency(BaseModel):
    idempotency_key : str
    event_id: UUID
    received_at: datetime



def add_data_to_tables(events:list[Dict[str, Any]] , idempotencies:list[Dict[str, Any]], session:Session):

    try:
        session.execute(insert(RawEvents),events)
        session.execute(insert(IdempotencyKey),idempotencies)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()



def main():
    session = SessionLocal()
    events = []
    idempotencies = []
    start_time = datetime.now(timezone.utc)
    event_types = ['login','logout','signIn','SignUp','purchase','payment','add to cart']
    meta_data_action = ["product_viewed","product_added_to_cart","checkout_started","payment_attempted","order_placed"]
    organizations = [ UUID("843379ba-a428-417a-b075-1e16e8c28d86"),UUID("135aaf82-466d-4650-a0e7-6637d9172827"),UUID("07fb5d2e-33a3-4cf3-b36e-b74098f942ad"),UUID("f8b6a7f7-605b-4186-978d-ca95798f87c8"),UUID("f9ef68fe-8863-49ee-936d-e17da86263c3") ]

    for i in range(4000):
        occurred_at = start_time + timedelta(minutes=33)
        received_at = start_time + timedelta(minutes=3)
        current_event_id = uuid4()

        events.append(SampleEvent(
            event_id = current_event_id,
            event_type=random.choice(event_types),
            occurred_at= occurred_at,
            received_at = received_at,
            user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
            organization_id = random.choice(organizations),
            event_metadata = {
                                    "action": random.choice(meta_data_action),
                                    "product_id": ''.join(random.choices(string.ascii_letters + string.digits, k=6)),
                                    "quantity": random.randint(1,10),
                                    "payment_method": random.choice(["card", "upi", "netbanking", "wallet"]),
                                }
        )
        )

        idempotencies.append(SampleIdempotency(
            idempotency_key=f"{i}-{''.join(random.choices(string.ascii_letters + string.digits, k=8))}",
            event_id=current_event_id,
            received_at=occurred_at
        ))

        start_time = occurred_at


    event_rows = [event.model_dump() for event in events]
    idempotency_rows = [idempotency.model_dump() for idempotency in idempotencies]

    add_data_to_tables(event_rows,idempotency_rows,session)


if __name__ == "__main__":
    main()