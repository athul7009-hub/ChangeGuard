from tax import add_tax


def calculate_total(unit_price: float, quantity: int) -> float:
    subtotal = unit_price * quantity
    return round(add_tax(subtotal), 2)
