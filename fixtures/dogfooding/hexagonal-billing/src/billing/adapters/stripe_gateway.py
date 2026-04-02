from billing.domain.invoice import Invoice
from billing.ports.payment_gateway import PaymentGateway


class StripeGateway(PaymentGateway):
    def capture(self, invoice: Invoice) -> str:
        return f"captured:{invoice.invoice_id}"
