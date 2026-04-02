from checkout.service import total_after_discount


def test_total_after_discount_handles_missing_coupon() -> None:
    assert total_after_discount(5000, None) == 5000
