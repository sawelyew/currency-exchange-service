from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.broker import broker
from app.services.tasks import update_currency_rates_task
from app.core.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Запуск приложения и инициализация брокера Taskiq...")
    await broker.startup()
    logger.info("Запуск фоновой задачи обновления курсов валют...")
    await update_currency_rates_task.kiq()
    yield
    logger.info("Остановка брокера и выключение приложения...")
    await broker.shutdown()