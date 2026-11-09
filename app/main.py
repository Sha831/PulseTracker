from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from redis import Redis

from app.api.events import router as events_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
from app.scheduler.aggregate_job import aggregate_job
from app.core.config import REDIS_URL


@asynccontextmanager
async def lifespan(app: FastAPI):

    app.state.redis_client = Redis.from_url(
        url=REDIS_URL,
        decode_responses=True
    )

    scheduler = None

    if app.state.start_scheduler:
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            aggregate_job,
            trigger="cron",
            minute=0
        )
        scheduler.start()

    yield

    if scheduler and scheduler.running:
        scheduler.shutdown()

    app.state.redis_client.close()


app = FastAPI(lifespan=lifespan)
app.state.start_scheduler = True

app.include_router(events_router)
app.include_router(auth_router)
app.include_router(analytics_router)
