from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Product:
    """
    Один товар из чека.
    """

    name: str
    price: float
    quantity: int = 1

    unit_price: float | None = None

    vat: str | None = None

    discount: float | None = None


@dataclass(slots=True)
class ReceiptData:
    """
    Полностью распознанный чек.
    """

    shop_name: str | None = None

    receipt_number: str | None = None

    receipt_date: datetime | None = None

    total: float | None = None

    payment_type: str | None = None

    currency: str = "PLN"

    products: list[Product] = field(default_factory=list)

    raw_text: str = ""


@dataclass(slots=True)
class OCRResult:
    """
    Результат работы OCR.
    """

    success: bool

    text: str

    lines: list[str]

    receipt: ReceiptData | None = None

    error: str | None = None