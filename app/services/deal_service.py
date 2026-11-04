import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import ExchangeRate
from app.models.deal import DealStatus
from app.repositories.deal import DealRepository
from app.schemas.deal import PendingDeal, PendingDealResponse, DealInitiateResponse, AnalyticsResponse, AnalyticsItem
from app.core.logger import get_logger

logger = get_logger(__name__)


class DealService:
    @staticmethod
    async def _get_currency_rate(
            session: AsyncSession,
            currency_code: str
    ) -> Decimal:
        if currency_code.upper() == "BYN":
            return Decimal("1.0")

        result = await session.execute(
            select(ExchangeRate)
            .filter(ExchangeRate.currency_code == currency_code.upper())
            .order_by(ExchangeRate.rate_date.desc())
        )
        currency = result.scalars().first()
        if not currency:
            logger.warning(f"Курс для валюты {currency_code} не найден в базе")
            raise HTTPException(
                status_code=404,
                detail=f"Курс для валюты {currency_code} не найден в базе. Обновите справочник."
            )
        return currency.rate

    @staticmethod
    async def get_pending_deals(
            session: AsyncSession
    ) -> PendingDealResponse:
        logger.info("Запрос списка незавершенных сделок")
        repo = DealRepository(session)
        deals = await repo.get_pending_deals()

        mapped_deals = [
            PendingDeal(
                id=deal.id,
                source_currency=deal.source_currency,
                target_currency=deal.target_currency,
                source_amount=deal.source_amount,
                target_amount=deal.target_amount,
                rate=deal.rate,
            )
            for deal in deals
        ]

        return PendingDealResponse(deals=mapped_deals)

    @classmethod
    async def initiate_deal(
            cls,
            session: AsyncSession,
            source_currency: str,
            target_currency: str,
            source_amount: Decimal
    ) -> DealInitiateResponse:
        src = source_currency.upper()
        tgt = target_currency.upper()

        logger.info(f"Инициализация сделки: {source_amount} {src} -> {tgt}")

        source_rate = await cls._get_currency_rate(session, src)
        target_rate = await cls._get_currency_rate(session, tgt)

        amount_in_byn = source_amount * source_rate
        target_amount = amount_in_byn / target_rate

        exchange_rate = source_rate / target_rate

        repo = DealRepository(session)
        deal = await repo.create_deal(
            source_currency=src,
            target_currency=tgt,
            source_amount=source_amount,
            target_amount=target_amount.quantize(Decimal("0.0001")),
            rate=exchange_rate.quantize(Decimal("0.0001"))
        )

        logger.info(f"Сделка успешно создана с ID: {deal.id}")

        return DealInitiateResponse(
            deal_id=deal.id,
            target_amount=deal.target_amount,
            rate=deal.rate,
        )

    @staticmethod
    async def process_deal_action(
            session: AsyncSession,
            deal_id: uuid.UUID,
            action: str
    ):
        logger.info(f"Обработка действия '{action}' для сделки ID: {deal_id}")
        repo = DealRepository(session)
        deal = await repo.get_by_id(deal_id)

        if not deal:
            logger.warning(f"Сделка с ID {deal_id} не найдена")
            raise HTTPException(status_code=404, detail="Сделка не найдена.")

        if deal.status != DealStatus.PENDING:
            logger.warning(f"Попытка обработать уже закрытую сделку ID {deal_id} со статусом {deal.status}")
            raise HTTPException(
                status_code=400,
                detail=f"Сделка уже обработана. Текущий статус: {deal.status}"
            )

        action_lower = action.lower()
        if action_lower == "confirm":
            new_status = DealStatus.CONFIRMED
            message = "Сделка успешно подтверждена и зафиксирована в системе."
        elif action_lower == "decline":
            new_status = DealStatus.DECLINED
            message = "Сделка отклонена."
        else:
            logger.warning(f"Передано неверное действие: {action}")
            raise HTTPException(status_code=400, detail="Неверное действие. Используйте 'CONFIRM' или 'DECLINE'.")

        updated_deal = await repo.update_status(deal, new_status)
        logger.info(f"Сделка ID {deal_id} успешно переведена в статус {new_status}")

        return {
            "deal_id": updated_deal.id,
            "status": updated_deal.status,
            "message": message
        }

    @staticmethod
    async def get_analytics(
            session: AsyncSession,
            date_from: datetime,
            date_to: datetime,
            currency: Optional[str] = None
    ) -> AnalyticsResponse:
        logger.info(f"Запрос аналитики с {date_from} по {date_to} для валюты: {currency or 'все'}")
        repo = DealRepository(session)
        raw_analytics = await repo.get_analytics(date_from=date_from, date_to=date_to, currency=currency)

        analytics_items = [
            AnalyticsItem(
                currency=item["currency"],
                incoming_amount=item["incoming_amount"],
                outgoing_amount=item["outgoing_amount"],
                deals_count=item["deals_count"]
            )
            for item in raw_analytics
        ]

        return AnalyticsResponse(analytics=analytics_items)