from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler

from app.api.events import router as events_router
from app.api.auth import router as auth_router
from app.api.analytics import router as analytics_router
from app.scheduler.aggregate_job import aggregate_job


scheduler = BackgroundScheduler()
scheduler.add_job(aggregate_job, trigger='cron',minute=0)

@asynccontextmanager
async def lifespan(app: FastAPI):

    scheduler.start()

    yield

    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(events_router)
app.include_router(auth_router)
app.include_router(analytics_router)





