"""The indexes we rank: which file and column each comes from, and a
readable name and group for it."""

import pandas as pd

from .french import download, first_monthly_table

INDUSTRIES = {
    "Agric": "Agriculture", "Food": "Food Products", "Soda": "Candy & Soda", "Beer": "Beer & Liquor",
    "Smoke": "Tobacco", "Toys": "Recreation", "Fun": "Entertainment", "Books": "Printing & Publishing",
    "Hshld": "Consumer Goods", "Clths": "Apparel", "Hlth": "Healthcare", "MedEq": "Medical Equipment",
    "Drugs": "Pharmaceuticals", "Chems": "Chemicals", "Rubbr": "Rubber & Plastics", "Txtls": "Textiles",
    "BldMt": "Construction Materials", "Cnstr": "Construction", "Steel": "Steel", "FabPr": "Fabricated Products",
    "Mach": "Machinery", "ElcEq": "Electrical Equipment", "Autos": "Autos & Trucks", "Aero": "Aircraft",
    "Ships": "Ships & Railroad Equipment", "Guns": "Defense", "Gold": "Precious Metals", "Mines": "Industrial Mining",
    "Coal": "Coal", "Oil": "Oil & Gas", "Util": "Utilities", "Telcm": "Telecom", "PerSv": "Personal Services",
    "BusSv": "Business Services", "Hardw": "Computers", "Softw": "Software", "Chips": "Electronic Equipment",
    "LabEq": "Measuring & Control Equipment", "Paper": "Business Supplies", "Boxes": "Shipping Containers",
    "Trans": "Transportation", "Whlsl": "Wholesale", "Rtail": "Retail", "Meals": "Restaurants & Hotels",
    "Banks": "Banking", "Insur": "Insurance", "RlEst": "Real Estate", "Fin": "Trading & Finance", "Other": "Everything Else",
}

DECILES = ["Lo 10", "2-Dec", "3-Dec", "4-Dec", "5-Dec", "6-Dec", "7-Dec", "8-Dec", "9-Dec", "Hi 10"]
MOMENTUM = ["Lo PRIOR"] + [f"PRIOR {n}" for n in range(2, 10)] + ["Hi PRIOR"]

# (file, group, how to name decile n of 1..10)
DECILE_FILES = [
    ("Portfolios_Formed_on_ME", "Size", lambda n: f"Size decile {n}" + (" (smallest)" if n == 1 else " (largest)" if n == 10 else "")),
    ("Portfolios_Formed_on_BE-ME", "Value", lambda n: f"Value decile {n}" + (" (growth)" if n == 1 else " (deep value)" if n == 10 else "")),
    ("10_Portfolios_Prior_12_2", "Momentum", lambda n: f"Momentum decile {n}" + (" (losers)" if n == 1 else " (winners)" if n == 10 else "")),
    ("Portfolios_Formed_on_OP", "Profitability", lambda n: f"Profitability decile {n}" + (" (least)" if n == 1 else " (most)" if n == 10 else "")),
    ("Portfolios_Formed_on_INV", "Investment", lambda n: f"Investment decile {n}" + (" (conservative)" if n == 1 else " (aggressive)" if n == 10 else "")),
]

SIZE_WORDS = {1: "Smallest", 2: "Small", 3: "Mid", 4: "Large", 5: "Largest"}
VALUE_WORDS = {1: "growth", 2: "growth-leaning", 3: "blend", 4: "value-leaning", 5: "value"}


def _grid_name(column):
    """'SMALL LoBM' / 'ME2 BM3' / 'BIG HiBM' -> 'Small growth' style names."""
    size_part, value_part = column.split()
    size = {"SMALL": 1, "BIG": 5}.get(size_part) or int(size_part[2])
    value = {"LoBM": 1, "HiBM": 5}.get(value_part) or int(value_part[2])
    return size, value, f"{SIZE_WORDS[size]} {VALUE_WORDS[value]}"


def load(cache_dir):
    """(returns, info, risk_free): monthly decimal returns with one column
    per index, a table describing each index, and the risk-free rate."""
    series, info = {}, []

    def add(key, name, group, values):
        series[key] = values
        info.append({"id": key, "name": name, "group": group})

    factors = first_monthly_table(download("F-F_Research_Data_Factors", cache_dir))
    risk_free = factors["RF"]
    add("market", "US Total Market", "Market", factors["Mkt-RF"] + factors["RF"])

    industries = first_monthly_table(download("49_Industry_Portfolios", cache_dir))
    for code, name in INDUSTRIES.items():
        add(f"ind-{code.lower()}", name, "Industry", industries[code])

    for file, group, label in DECILE_FILES:
        table = first_monthly_table(download(file, cache_dir))
        columns = MOMENTUM if group == "Momentum" else DECILES
        for n, column in enumerate(columns, start=1):
            add(f"{group.lower()}-{n}", label(n), group, table[column])

    grid = first_monthly_table(download("25_Portfolios_5x5", cache_dir))
    for column in grid.columns:
        size, value, name = _grid_name(column)
        add(f"sv-{size}{value}", name, "Size × Value", grid[column])

    returns = pd.DataFrame(series)
    return returns, pd.DataFrame(info).set_index("id"), risk_free
