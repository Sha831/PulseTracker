from fastapi import FastAPI

from app.api.events import router as events_router
from app.api.auth import router as auth_router

app = FastAPI()
app.include_router(events_router)
app.include_router(auth_router)

