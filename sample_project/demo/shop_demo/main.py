from pipeline import build_order_summary


def main():
    summary = build_order_summary("SKU-101", quantity=2)
    print(summary)


if __name__ == "__main__":
    main()
