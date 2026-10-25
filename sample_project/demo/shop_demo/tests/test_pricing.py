from shop_demo.pricing import calculate_total


def test_calculate_total_includes_tax():
    assert calculate_total(10.0, 2) == 22.0
