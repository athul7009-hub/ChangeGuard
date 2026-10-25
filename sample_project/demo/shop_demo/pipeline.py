from inventory import get_stock
from pricing import calculate_total


def build_order_summary(sku: str, quantity: int) -> dict:
    stock = get_stock(sku)
    total = calculate_total(unit_price=25.0, quantity=quantity)
    return {
        "sku": sku,
        "quantity": quantity,
        "stock": stock,
        "total": total,
    }
