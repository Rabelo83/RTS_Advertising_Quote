from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
from quote_pdf import build_quote_pdf_bytes
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

    # Map your QuoteResult -> frontend shape
    # QuoteResult fields (from your earlier code):
    #   line_breakdown, subtotal_base, total_after_discounts,
    #   discount_tier_used_exterior, discount_tier_used_interior, flags_summary
    saved_amount = round(totals.subtotal_base - totals.total_after_discounts, 2)

    return jsonify({
        "items": [{
            "type_display": i.type_display,
            "product": i.product,
            "code": i.code,
            "months": i.months,
            "qty": i.qty,
            "unit_price": i.unit_price,
            "line_total": i.line_total
        } for i in totals.line_breakdown],
        "subtotal_base": totals.subtotal_base,
        "total": totals.total_after_discounts,
        "saved": saved_amount,
        "exterior_tier": totals.discount_tier_used_exterior,
        "interior_tier": totals.discount_tier_used_interior,
        "flags": totals.flags_summary
    })

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    """
    JSON body:
      {
        "client_name": "Acme Co",
        "items": [{ "type_display": "Exterior", "variant": "Full Wrap", "months": 4, "qty": 2 }, ...],
        "discount_choice": "None" | "Agency 10%" | "PSA 10%",
        "upfront_selected": true | false
      }
    """
    data = request.get_json(force=True)

    client_name = data.get("client_name", "Unknown")

    # Convert front-end items array into the tuple format your compute_quote expects
    items_spec = []
    for it in data.get("items", []):
        items_spec.append((
            it["type_display"],
            it["variant"],
            int(it["months"]),
            int(it["qty"]),
        ))

    discount_choice = data.get("discount_choice", "None")
    upfront_selected = bool(data.get("upfront_selected", False))

    # Use your existing calculator
    result = compute_quote(items_spec, discount_choice, upfront_selected)

    # Build PDF in-memory and return as a download
    pdf_bytes = build_quote_pdf_bytes(client_name, result)
    buffer = BytesIO(pdf_bytes)

    # Safe filename
    safe_client = "".join(c for c in client_name if c.isalnum() or c in (" ","-","_")).strip().replace(" ", "_")
    filename = f"RTS_Quote_{safe_client or 'Client'}.pdf"

    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    # For local debug if you ever run it locally
    app.run(host="0.0.0.0", port=5000, debug=True)
