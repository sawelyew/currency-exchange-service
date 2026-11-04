import uuid
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import String, Numeric, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class DealStatus(str, PyEnum):
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    PENDING = "PENDING"


class Deal(Base, TimestampMixin):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    source_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    target_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    source_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)

    rate: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)

    status: Mapped[DealStatus] = mapped_column(
        SQLEnum(DealStatus),
        default=DealStatus.PENDING,
        nullable=False,
        index=True
    )