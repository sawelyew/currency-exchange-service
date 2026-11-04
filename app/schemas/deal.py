from typing import List, Optional
from decimal import Decimal
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.models.deal import DealStatus


class PendingDeal(BaseModel):
    id: uuid.UUID
    source_currency: str
    target_currency: str
    source_amount: Decimal
    target_amount: Decimal
    rate: Decimal

    model_config = ConfigDict(from_attributes=True)


class PendingDealResponse(BaseModel):
    deals: List[PendingDeal]


class DealInitiateRequest(BaseModel):
    source_currency: str = Field(
        ...,
        max_length=3,
        description="Исходная валюта",
        examples=["USD"]
    )
    target_currency: str = Field(
        ...,
        max_length=3,
        description="Целевая валюта",
        examples=["BYN"]
    )
    amount: Decimal = Field(
        ...,
        gt=0,
        description="Сумма в исходной валюте",
        examples=[Decimal("100.50")]
    )


class DealInitiateResponse(BaseModel):
    deal_id: uuid.UUID
    target_amount: Decimal
    rate: Decimal

    model_config = ConfigDict(from_attributes=True)


class DealActionRequest(BaseModel):
    deal_id: uuid.UUID = Field(
        ...,
        description="Идентификатор сделки",
        examples=[uuid.UUID("398fff15-77dc-4f80-81e4-39c859ca312d")]
    )
    action: str = Field(
        ...,
        description="Выберите действие: CONFIRM или DECLINE",
        examples=["CONFIRM"]
    )


class DealActionResponse(BaseModel):
    deal_id: uuid.UUID
    status: DealStatus
    message: str

    model_config = ConfigDict(from_attributes=True)


class AnalyticsItem(BaseModel):
    currency: str = Field(..., description="Код валюты", examples=["USD"])
    incoming_amount: Decimal = Field(..., description="Сумма, полученная в кассу", examples=[Decimal("1500.00")])
    outgoing_amount: Decimal = Field(..., description="Сумма, ушедшая из кассы", examples=[Decimal("0.00")])
    deals_count: int = Field(..., description="Количество сделок", examples=[5])

    model_config = ConfigDict(from_attributes=True)


class AnalyticsResponse(BaseModel):
    analytics: List[AnalyticsItem] = Field(
        ...,
        examples=[
            [
                {
                    "currency": "USD",
                    "incoming_amount": 1500.00,
                    "outgoing_amount": 0.00,
                    "deals_count": 5
                },
                {
                    "currency": "BYN",
                    "incoming_amount": 0.00,
                    "outgoing_amount": 4881.00,
                    "deals_count": 5
                }
            ]
        ]
    )


class AnalyticsFilter(BaseModel):
    date_from: datetime = Field(
        ...,
        description="Дата начала периода (например, 2026-01-01T00:00:00)",
        examples=["2026-01-01T00:00:00"]
    )
    date_to: datetime = Field(
        ...,
        description="Дата окончания периода (например, 2026-12-31T23:59:59)",
        examples=["2026-12-31T23:59:59"]
    )
    currency: Optional[str] = Field(
        None,
        max_length=3,
        description="Необязательный код валюты (например, USD)",
        examples=["USD"]
    )