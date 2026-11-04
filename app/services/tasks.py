from app.core.broker import broker
from app.core.database import AsyncSessionLocal
from app.services.nbrb_service import fetch_and_save_rates
from app.core.logger import get_logger

logger = get_logger(__name__)

@broker.task(
    schedule=[{"cron": "0 8 * * *"}],
    retries=3,
    retry_delay=10
)
async def update_currency_rates_task():
    async with AsyncSessionLocal() as session:
        try:
            await fetch_and_save_rates(session)
            logger.info("Курсы успешно обновлены и сохранены.")
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче: {e}")