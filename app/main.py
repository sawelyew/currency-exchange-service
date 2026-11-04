from fastapi import FastAPI
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.api import deal_router
from app.core.logger import setup_logging

app = FastAPI(
    title="Currency Exchange Service",
    version="1.0.0",
    lifespan=lifespan
)

setup_logging()

register_exception_handlers(app)
app.include_router(deal_router)