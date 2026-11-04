from fastapi import APIRouter, Depends
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.deal import *
from app.services.deal_service import DealService


router = APIRouter(prefix="/deals", tags=["Deals"])


@router.get("/pending")
async def get_pending_deals(
        session: Annotated[AsyncSession, Depends(get_db)]
) -> PendingDealResponse:
    return await DealService.get_pending_deals(session)


@router.post("/initiate")
async def initiate_deal_endpoint(
        payload: DealInitiateRequest,
        session: Annotated[AsyncSession, Depends(get_db)]
) -> DealInitiateResponse:
    deal = await DealService.initiate_deal(
        session=session,
        source_currency=payload.source_currency,
        target_currency=payload.target_currency,
        source_amount=payload.amount
    )
    return deal


@router.post("/action")
async def confirm_or_decline_deal_endpoint(
    payload: DealActionRequest,
    session: Annotated[AsyncSession, Depends(get_db)]
) -> DealActionResponse:
    result = await DealService.process_deal_action(
        session=session,
        deal_id=payload.deal_id,
        action=payload.action
    )
    return result


@router.get("/analytics")
async def get_deals_analytics_endpoint(
    filters: Annotated[AnalyticsFilter, Depends()],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AnalyticsResponse:
    return await DealService.get_analytics(
        session=session,
        date_from=filters.date_from,
        date_to=filters.date_to,
        currency=filters.currency
    )