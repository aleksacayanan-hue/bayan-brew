"""Generate synthetic Bayan Brew POS line items. Run: python generate_transactions.py"""
from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 20261001
random.seed(SEED)

OUT_DIR = Path(__file__).resolve().parent

STORES = [
    ("ST01", "Bayan Brew SM North", "Quezon City", "Metro Manila"),
    ("ST02", "Bayan Brew Trinoma", "Quezon City", "Metro Manila"),
    ("ST03", "Bayan Brew MOA", "Pasay", "Metro Manila"),
    ("ST04", "Bayan Brew BGC High Street", "Taguig", "Metro Manila"),
    ("ST05", "Bayan Brew Eastwood", "Quezon City", "Metro Manila"),
    ("ST06", "Bayan Brew Ayala Cebu", "Cebu City", "Central Visayas"),
    ("ST07", "Bayan Brew SM Davao", "Davao City", "Davao Region"),
    ("ST08", "Bayan Brew Robinsons Iloilo", "Iloilo City", "Western Visayas"),
    ("ST09", "Bayan Brew Marquee Mall", "Angeles", "Central Luzon"),
    ("ST10", "Bayan Brew SM Baguio", "Baguio", "Cordillera"),
]

# (product_id, name, category, base_price_small)
PRODUCTS = [
    ("PR01", "Classic Milk Tea", "Milk Tea", 89),
    ("PR02", "Wintermelon Milk Tea", "Milk Tea", 89),
    ("PR03", "Okinawa Milk Tea", "Milk Tea", 99),
    ("PR04", "Taro Milk Tea", "Milk Tea", 109),
    ("PR05", "Brown Sugar Fresh Milk", "Signature", 129),
    ("PR06", "Matcha Latte", "Latte", 119),
    ("PR07", "Coffee Jelly Milk Tea", "Milk Tea", 109),
    ("PR08", "Fruit Tea Green Apple", "Fruit Tea", 79),
    ("PR09", "Fruit Tea Passion", "Fruit Tea", 79),
    ("PR10", "Cheese Foam Jasmine", "Premium", 139),
    ("PR11", "Salted Cream Black Tea", "Premium", 129),
    ("PR12", "Chocolate Oreo Smoothie", "Smoothie", 119),
    ("PR13", "Mango Snow", "Smoothie", 129),
    ("PR14", "Egg Pudding Add-on", "Add-on", 25),
    ("PR15", "Pearl Add-on", "Add-on", 15),
]

SIZE_MULT = {"Small": 1.0, "Medium": 1.15, "Large": 1.3}
SIZE_WEIGHTS = [0.25, 0.55, 0.20]

START = date(2025, 1, 1)
END = date(2025, 9, 30)


def business_multiplier(d: date) -> float:
    m = 1.0
    if d.weekday() >= 5:
        m *= 1.35
    if d.month in (4, 5, 12):
        m *= 1.12
    return m


def store_weight(store_id: str) -> float:
    if store_id in ("ST03", "ST04"):
        return 1.4
    if store_id in ("ST06", "ST07"):
        return 1.15
    return 1.0


def write_csv(path: Path, headers: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main() -> None:
    store_rows = [
        [sid, name, city, region] for sid, name, city, region in STORES
    ]
    write_csv(
        OUT_DIR / "bayan-brew-stores.csv",
        ["StoreID", "StoreName", "City", "Region"],
        store_rows,
    )

    product_rows = [
        [pid, name, cat, base] for pid, name, cat, base in PRODUCTS
    ]
    write_csv(
        OUT_DIR / "bayan-brew-products.csv",
        ["ProductID", "ProductName", "Category", "BasePriceSmall"],
        product_rows,
    )

    transactions: list[list] = []
    order_seq = 1
    d = START
    product_ids = [p[0] for p in PRODUCTS]
    main_products = [p for p in PRODUCTS if p[3] != "Add-on" or p[2] != "Add-on"]
    main_ids = [p[0] for p in PRODUCTS if p[2] != "Add-on"]
    addon_ids = [p[0] for p in PRODUCTS if p[2] == "Add-on"]
    product_by_id = {p[0]: p for p in PRODUCTS}

    while d <= END:
        base_orders = random.randint(45, 95)
        n_orders = int(base_orders * business_multiplier(d))
        for _ in range(n_orders):
            store = random.choices(
                STORES,
                weights=[store_weight(s[0]) for s in STORES],
                k=1,
            )[0]
            order_id = f"ORD-{d.strftime('%Y%m%d')}-{order_seq:05d}"
            order_seq += 1
            hour = random.choices(
                range(10, 22),
                weights=[1, 1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2],
                k=1,
            )[0]
            minute = random.randint(0, 59)
            ts = datetime(d.year, d.month, d.day, hour, minute)

            n_lines = random.choices([1, 2, 3], weights=[0.55, 0.35, 0.10], k=1)[0]
            line_pids = [random.choice(main_ids) for _ in range(n_lines)]
            if random.random() < 0.22:
                line_pids.append(random.choice(addon_ids))

            for pid in line_pids:
                p = product_by_id[pid]
                if p[2] == "Add-on":
                    size = "N/A"
                    qty = 1
                    unit = p[3]
                else:
                    size = random.choices(
                        list(SIZE_MULT), weights=SIZE_WEIGHTS, k=1
                    )[0]
                    qty = random.choices([1, 2], weights=[0.92, 0.08], k=1)[0]
                    unit = round(p[3] * SIZE_MULT[size], 2)

                line_total = round(unit * qty, 2)
                transactions.append(
                    [
                        order_id,
                        ts.strftime("%Y-%m-%d"),
                        ts.strftime("%H:%M"),
                        store[0],
                        pid,
                        size,
                        qty,
                        unit,
                        line_total,
                    ]
                )

        d += timedelta(days=1)

    write_csv(
        OUT_DIR / "bayan-brew-transactions.csv",
        [
            "OrderID",
            "OrderDate",
            "OrderTime",
            "StoreID",
            "ProductID",
            "Size",
            "Quantity",
            "UnitPricePHP",
            "LineRevenuePHP",
        ],
        transactions,
    )

    print(f"Wrote {len(store_rows)} stores, {len(product_rows)} products, {len(transactions)} transaction lines.")


if __name__ == "__main__":
    main()
