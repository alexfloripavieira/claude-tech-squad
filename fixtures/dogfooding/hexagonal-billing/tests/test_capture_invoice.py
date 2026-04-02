from billing.adapters.stripe_gateway import StripeGateway
from billing.domain.invoice import Invoice


def test_capture_invoice_returns_capture_reference() -> None:
    gateway = StripeGateway()
    invoice = Invoice(invoice_id="inv-123", amount_cents=2500)

    assert gateway.capture(invoice) == "captured:inv-123"
