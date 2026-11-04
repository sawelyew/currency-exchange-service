import httpx
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.currency import ExchangeRate
from app.core.logger import get_logger

logger = get_logger(__name__)


async def fetch_and_save_rates(session: AsyncSession) -> None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(settings.NBRB_API_URL, timeout=10.0)
            response.raise_for_status()
            rates_data = response.json()
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при запросе к НБ РБ: {e}")
            return

    today = date.today()

    for item in rates_data:
        cur_abbreviation = item.get("Cur_Abbreviation")
        cur_scale = item.get("Cur_Scale", 1)
        cur_official_rate = item.get("Cur_OfficialRate")

        if not cur_official_rate or not cur_abbreviation:
            continue

        rate_value = Decimal(str(cur_official_rate)) / Decimal(str(cur_scale))

        stmt = select(ExchangeRate).where(
            ExchangeRate.currency_code == cur_abbreviation,
            ExchangeRate.rate_date == today
        )
        result = await session.execute(stmt)
        existing_rate = result.scalar_one_or_none()

        if existing_rate:
            existing_rate.rate = rate_value
        else:
            new_rate = ExchangeRate(
                currency_code=cur_abbreviation,
                rate=rate_value,
                rate_date=today
            )
            session.add(new_rate)

    await session.commit()
    logger.info("Курсы валют успешно обновлены и синхронизированы с БД.")