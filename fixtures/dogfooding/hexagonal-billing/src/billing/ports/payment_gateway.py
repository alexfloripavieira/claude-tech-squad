from typing import Protocol

from billing.domain.invoice import Invoice


class PaymentGateway(Protocol):
    def capture(self, invoice: Invoice) -> str:
        ...
