from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from app.repositories.base import BaseRepository
from app.models.deal import Deal, DealStatus


class DealRepository(BaseRepository[Deal]):
    def __init__(self, session: AsyncSession):
        super().__init__(Deal, session)

    async def get_pending_deals(self) -> List[Deal]:
        result = await self.session.execute(
            select(Deal).filter(Deal.status == DealStatus.PENDING)
        )
        return result.scalars().all()

    async def create_deal(
            self,
            source_currency: str,
            target_currency: str,
            source_amount: Decimal,
            target_amount: Decimal,
            rate: Decimal
    ) -> Deal:
        deal = Deal(
            source_currency=source_currency.upper(),
            target_currency=target_currency.upper(),
            source_amount=source_amount,
            target_amount=target_amount,
            rate=rate,
            status=DealStatus.PENDING
        )
        return await self.save(deal)

    async def update_status(self, deal: Deal, status: DealStatus) -> Deal:
        deal.status = status
        return await self.save(deal)

    async def get_analytics(
            self,
            date_from: datetime,
            date_to: datetime,
            currency: Optional[str] = None
    ) -> List[dict]:
        query = select(Deal).filter(
            Deal.status == DealStatus.CONFIRMED,
            Deal.created_at >= date_from,
            Deal.created_at <= date_to
        )

        if currency:
            curr_upper = currency.upper()
            query = query.filter(
                or_(
                    Deal.source_currency == curr_upper,
                    Deal.target_currency == curr_upper
                )
            )

        result = await self.session.execute(query)
        deals = result.scalars().all()

        stats = {}

        for deal in deals:
            src = deal.source_currency
            tgt = deal.target_currency

            if src not in stats:
                stats[src] = {"incoming": Decimal("0"), "outgoing": Decimal("0"), "count": 0}
            if tgt not in stats:
                stats[tgt] = {"incoming": Decimal("0"), "outgoing": Decimal("0"), "count": 0}

            stats[src]["incoming"] += deal.source_amount
            stats[src]["count"] += 1

            stats[tgt]["outgoing"] += deal.target_amount
            stats[tgt]["count"] += 1

        if currency:
            curr_upper = currency.upper()
            filtered_stats = {
                curr_upper: stats.get(curr_upper, {"incoming": Decimal("0"), "outgoing": Decimal("0"), "count": 0})}
            stats = filtered_stats

        analytics_list = [
            {
                "currency": curr,
                "incoming_amount": data["incoming"],
                "outgoing_amount": data["outgoing"],
                "deals_count": data["count"]
            }
            for curr, data in stats.items()
        ]

        return analytics_list