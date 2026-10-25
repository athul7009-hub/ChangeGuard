STOCK = {
    "SKU-101": 12,
    "SKU-202": 4,
}


def get_stock(sku: str) -> int:
    return STOCK.get(sku, 0)
