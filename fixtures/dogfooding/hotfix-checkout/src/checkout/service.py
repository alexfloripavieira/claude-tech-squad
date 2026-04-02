def total_after_discount(subtotal_cents: int, discount_cents: int | None) -> int:
    return subtotal_cents - (discount_cents or 0)
