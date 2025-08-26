from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---------- TABLES ----------
EXTERIOR_RATE_TABLE: Dict[str, Dict[str, List[float]]] = {
    "Full Wrap": {
        "FW-4":  [4500.0, 4050.0, 3600.0, 3150.0],
        "FW-8":  [8800.0, 7920.0, 7040.0, 6160.0],
        "FW-12": [12000.0, 10800.0, 9600.0, 8400.0],
        "FW-24": [24000.0, 21600.0, 19200.0, 16800.0],
    },
    "King Kong": {
        "KK-1":  [900.0, 810.0, 720.0, 630.0],
        "KK-4":  [3420.0, 3078.0, 2736.0, 2394.0],
        "KK-8":  [6480.0, 5832.0, 5184.0, 4536.0],
        "KK-12": [9180.0, 8262.0, 7344.0, 6426.0],
    },
    "Kong": {
        "K-1":   [700.0, 630.0, 560.0, 490.0],
        "K-4":   [2660.0, 2394.0, 2128.0, 1862.0],
        "K-8":   [5040.0, 4536.0, 4032.0, 3528.0],
        "K-12":  [7140.0, 6426.0, 5712.0, 4998.0],
    },
    "King (St. Side)": {
        "Ksts-1":  [450.0, 405.0, 360.0, 315.0],
        "Ksts-4":  [1710.0, 1539.0, 1368.0, 1197.0],
        "Ksts-8":  [3240.0, 2916.0, 2592.0, 2268.0],
        "Ksts-12": [4590.0, 4131.0, 3672.0, 3213.0],
    },
    "Queen (Curb Side)": {
        "Qcs-1":  [350.0, 315.0, 280.0, 245.0],
        "Qcs-4":  [1330.0, 1197.0, 1064.0, 931.0],
        "Qcs-8":  [2520.0, 2268.0, 2016.0, 1764.0],
        "Qcs-12": [3570.0, 3213.0, 2856.0, 2499.0],
    },
}
EXTERIOR_ALLOWED_MONTHS = {
    "Full Wrap": [4, 8, 12, 24],
    "King Kong": [1, 4, 8, 12],
    "Kong": [1, 4, 8, 12],
    "King (St. Side)": [1, 4, 8, 12],
    "Queen (Curb Side)": [1, 4, 8, 12],
}

INTERIOR_RATE_TABLE: Dict[str, List[float]] = {
    "11x17": [680.0, 612.0],
    "11x28": [820.0, 738.0],
    "11x35": [960.0, 864.0],
    "11x42": [1000.0, 900.0],
}

AGENCY_OR_PSA_FLAG = "Agency/PSA"
UPFRONT_FLAG = "Upfront (Exterior)"
SIX_PLUS_FLAG = "6+ Buses (Exterior)"

# ---------- MODELS ----------
@dataclass
class LineItem:
    type_display: str   # "Exterior" | "Interior"
    product: str        # "Full Wrap" | "Interior Cards"
    code: str           # e.g., "FW-4" or "11x28"
    months: int
    qty: int
    unit_price: float
    line_total: float

@dataclass
class QuoteTotals:
    items: List[LineItem]
    subtotal_base: float
    total: float
    exterior_tier: int
    interior_tier: int
    flags_summary: str
    saved: float

# ---------- HELPERS ----------
def exterior_code(product: str, months: int) -> str:
    prefix = {"Full Wrap": "FW", "King Kong": "KK", "Kong": "K",
              "King (St. Side)": "Ksts", "Queen (Curb Side)": "Qcs"}[product]
    return f"{prefix}-{months}"

# ---------- CORE ----------
def compute_quote(items_spec, discount_choice: str, upfront_selected: bool) -> QuoteTotals:
    # items_spec: list of tuples: ("Exterior"|"Interior", variant, months, qty)
    total_exterior_qty = sum(q for t, _, _, q in items_spec if t == "Exterior")
    six_plus = total_exterior_qty >= 6

    flags = []
    if discount_choice in ("Agency 10%", "PSA 10%"): flags.append(AGENCY_OR_PSA_FLAG)
    if upfront_selected:                              flags.append(UPFRONT_FLAG)
    if six_plus:                                      flags.append(SIX_PLUS_FLAG)

    items: List[LineItem] = []
    base_subtotal = 0.0
    discounted_subtotal = 0.0
    used_tier_ext = 0
    used_tier_int = 0

    for t, variant, months, qty in items_spec:
        if t == "Exterior":
            tier = 0
            if AGENCY_OR_PSA_FLAG in flags: tier += 1
            if UPFRONT_FLAG in flags:       tier += 1
            if SIX_PLUS_FLAG in flags:      tier += 1
            tier = min(tier, 3)
            code = exterior_code(variant, months)
            row = EXTERIOR_RATE_TABLE[variant][code]
            base_unit = row[0]
            chosen_unit = row[tier]
            base_subtotal       += base_unit   * qty
            discounted_subtotal += chosen_unit * qty
            items.append(LineItem("Exterior", variant, code, months, qty, chosen_unit, chosen_unit*qty))
            used_tier_ext = max(used_tier_ext, tier)
        else:
            tier = 1 if (AGENCY_OR_PSA_FLAG in flags) else 0
            tier = min(tier, 1)
            per_month = INTERIOR_RATE_TABLE[variant][tier]
            base_unit = INTERIOR_RATE_TABLE[variant][0] * months
            chosen_unit = per_month * months
            base_subtotal       += base_unit   * qty
            discounted_subtotal += chosen_unit * qty
            items.append(LineItem("Interior", "Interior Cards", variant, months, qty, chosen_unit, chosen_unit*qty))
            used_tier_int = max(used_tier_int, tier)

    flags_used = []
    if AGENCY_OR_PSA_FLAG in flags: flags_used.append("Agency/PSA 10%")
    if upfront_selected:             flags_used.append("Upfront 10% (Exterior)")
    if six_plus:                     flags_used.append("6+ Buses 10% (Exterior)")
    flags_summary = ", ".join(flags_used) if flags_used else "None"

    saved = round(base_subtotal - discounted_subtotal, 2)

    return QuoteTotals(
        items=items,
        subtotal_base=round(base_subtotal, 2),
        total=round(discounted_subtotal, 2),
        exterior_tier=used_tier_ext,
        interior_tier=used_tier_int,
        flags_summary=flags_summary,
        saved=saved,
    )
