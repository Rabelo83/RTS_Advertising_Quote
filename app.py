from flask import Flask, render_template, request, jsonify
from rate_tables import (
    EXTERIOR_RATE_TABLE, EXTERIOR_ALLOWED_MONTHS, INTERIOR_RATE_TABLE,
    compute_quote
)

app = Flask(__name__)

@app.route("/")
def index():
    # pass options to the page (for dropdowns)
    exterior_products = list(EXTERIOR_RATE_TABLE.keys())
    interior_sizes = list(INTERIOR_RATE_TABLE.keys())
    allowed_months = EXTERIOR_ALLOWED_MONTHS  # used by JS
    return render_template(
        "index.html",
        exterior_products=exterior_products,
        interior_sizes=interior_sizes,
        allowed_months=allowed_months
    )

@app.route("/quote", methods=["POST"])
def quote():
    data = request.get_json(force=True)
    # items: [{type_display, variant, months, qty}, ...]
    items_spec = []
    for it in data.get("items", []):
        items_spec.append((it["type_display"], it["variant"], int(it["months"]), int(it["qty"])))

    discount_choice = data.get("discount_choice", "None")  # "None", "Agency 10%", "PSA 10%"
    upfront = bool(data.get("upfront_selected", False))

    totals = compute_quote(items_spec, discount_choice, upfront)

    return jsonify({
        "items": [{
            "type_display": i.type_display,
            "product": i.product,
            "code": i.code,
            "months": i.months,
            "qty": i.qty,
            "unit_price": i.unit_price,
            "line_total": i.line_total
        } for i in totals.items],
        "subtotal_base": totals.subtotal_base,
        "total": totals.total,
        "saved": totals.saved,
        "exterior_tier": totals.exterior_tier,
        "interior_tier": totals.interior_tier,
        "flags": totals.flags_summary
    })

if __name__ == "__main__":
    # For local debug if you ever run it locally
    app.run(host="0.0.0.0", port=5000, debug=True)
