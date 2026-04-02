from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    invoice_id: str
    amount_cents: int
