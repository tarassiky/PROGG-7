class Shipment:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.status = "CREATED"

    def cancel(self) -> None:
        self.status = "CANCELLED"