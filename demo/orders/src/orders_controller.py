"""HTTP-shaped entry. Handle is correct; two planted problems sit beside it."""

from src.orders_service import OrderService


class OrdersController:
    def __init__(self) -> None:
        self.svc = OrderService()

    def handle(self, body: dict) -> dict:
        prices = body["prices"]
        percent = int(body.get("percent", 0))
        return {"total": self.svc.quote(prices, percent)}

    def fn(self, body: dict) -> dict:
        """Opaque name. Same work as handle."""
        return self.handle(body)

    def status(self) -> str:
        return stauts
