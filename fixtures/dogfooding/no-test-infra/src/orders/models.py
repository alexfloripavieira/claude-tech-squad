class Order:
    def __init__(self, total: float):
        self.total = total

    def is_eligible_for_discount(self) -> bool:
        return self.total > 100.0
