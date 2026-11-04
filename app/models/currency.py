from decimal import Decimal
from datetime import date
from sqlalchemy import String, Numeric, Date, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin


class ExchangeRate(Base, TimestampMixin):
    __tablename__ = "exchange_rates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency_code: Mapped[str] = mapped_column(String(3), index=True, nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=4), nullable=False)
    rate_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("currency_code", "rate_date", name="uq_currency_date"),
    )