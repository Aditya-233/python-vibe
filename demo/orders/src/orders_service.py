"""Quote an order. Nothing here is tested yet."""


class OrderService:
    def total(self, prices: list[int]) -> int:
        return sum(prices)

    def quote(self, prices: list[int], percent: int) -> int:
        raw = self.total(prices)
        return raw - (raw * percent) // 100
