from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO

from quote_pdf import build_quote_pdf_bytes
from rate_tables import (
    EXTERIOR_RATE_TABLE,
    EXTERIOR_ALLOWED_MONTHS,
    INTERIOR_RATE_TABLE,
    compute_quote,  # returns QuoteTotals: items, subtotal_base, total, exterior_tier, interior_tier, flags_summary, saved
)

app = Flask(__name__)

@app.route("/")
def index():
    exterior_products = list(EXTERIOR_RATE_TABLE.keys())
    interior_sizes = list(INTERIOR_RATE_TABLE.keys())
    allowed_months = EXTERIOR_ALLOWED_MONTHS
    return render_template(
        "index.html",
        exterior_products=exterior_products,
        interior_sizes=interior_sizes,
        allowed_months=allowed_months,
    )

@app.route("/quote", methods=["POST"])
def quote():
    try:
        data = request.get_json(force=True) or {}

        items_spec = []
        for it in data.get("items", []):
            items_spec.append((
                it["type_display"],  # "Exterior" | "Interior"
                it["variant"],       # e.g., "Full Wrap" | "11x28"
                int(it["months"]),
                int(it["qty"]),
            ))

        discount_choice   = data.get("discount_choice", "None")
        upfront_selected  = bool(data.get("upfront_selected", False))

        totals = compute_quote(items_spec, discount_choice, upfront_selected)
        # totals is QuoteTotals with fields: items, subtotal_base, total, exterior_tier, interior_tier, flags_summary, saved

        return jsonify({
            "items": [{
                "type_display": i.type_display,
                "product": i.product,
                "code": i.code,
                "months": i.months,
                "qty": i.qty,
                "unit_price": i.unit_price,
                "line_total": i.line_total,
            } for i in totals.items],
            "subtotal_base": totals.subtotal_base,
            "total": totals.total,
            "saved": totals.saved,
            "exterior_tier": totals.exterior_tier,
            "interior_tier": totals.interior_tier,
            "flags": totals.flags_summary,
        })
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 400

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    try:
        data = request.get_json(force=True) or {}

        client_name = data.get("client_name", "Unknown")

        items_spec = []
        for it in data.get("items", []):
            items_spec.append((
                it["type_display"],
                it["variant"],
                int(it["months"]),
                int(it["qty"]),
            ))

        discount_choice  = data.get("discount_choice", "None")
        upfront_selected = bool(data.get("upfront_selected", False))

        result = compute_quote(items_spec, discount_choice, upfront_selected)

        pdf_bytes = build_quote_pdf_bytes(client_name, result)
        buffer = BytesIO(pdf_bytes)

        safe_client = "".join(c for c in client_name if c.isalnum() or c in (" ","-","_")).strip().replace(" ", "_")
        filename = f"RTS_Quote_{safe_client or 'Client'}.pdf"

        return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=filename)
    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
