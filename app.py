from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO

# Local modules
from quote_pdf import build_quote_pdf_bytes
from rate_tables import (
    EXTERIOR_RATE_TABLE,
    EXTERIOR_ALLOWED_MONTHS,
    INTERIOR_RATE_TABLE,
    compute_quote,  # returns QuoteResult with: line_breakdown, subtotal_base, total_after_discounts, discount_tier_used_exterior, discount_tier_used_interior, flags_summary
)

app = Flask(__name__)


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """
    Render the UI and inject dropdown data.
    """
    exterior_products = list(EXTERIOR_RATE_TABLE.keys())
    interior_sizes = list(INTERIOR_RATE_TABLE.keys())
    allowed_months = EXTERIOR_ALLOWED_MONTHS  # dict[str, list[int]]

    return render_template(
        "index.html",
        exterior_products=exterior_products,
        interior_sizes=interior_sizes,
        allowed_months=allowed_months,
    )


# -----------------------------------------------------------------------------
# API: Calculate quote
# -----------------------------------------------------------------------------
@app.route("/quote", methods=["POST"])
def quote():
    """
    Request JSON:
      {
        "items": [
          {"type_display":"Exterior","variant":"Full Wrap","months":4,"qty":2},
          {"type_display":"Interior","variant":"11x17","months":1,"qty":1}
        ],
        "discount_choice": "None" | "Agency 10%" | "PSA 10%",
        "upfront_selected": true|false
      }
    Response JSON:
      {
        items: [...],
        subtotal_base: float,
        total: float,          # table-driven total (already discounted by tier)
        saved: float,          # subtotal - total
        exterior_tier: int,    # 0..3
        interior_tier: int,    # 0..1
        flags: str
      }
    """
    try:
        data = request.get_json(force=True) or {}

        # Build items_spec expected by compute_quote
        items_spec = []
        for it in data.get("items", []):
            items_spec.append((
                it["type_display"],             # "Exterior" | "Interior"
                it["variant"],                  # e.g., "Full Wrap" | "11x28"
                int(it["months"]),
                int(it["qty"]),
            ))

        discount_choice = data.get("discount_choice", "None")
        upfront_selected = bool(data.get("upfront_selected", False))

        totals = compute_quote(items_spec, discount_choice, upfront_selected)

        saved_amount = round(totals.subtotal_base - totals.total_after_discounts, 2)

        return jsonify({
            "items": [{
                "type_display": i.type_display,
                "product": i.product,
                "code": i.code,
                "months": i.months,
                "qty": i.qty,
                "unit_price": i.unit_price,
                "line_total": i.line_total,
            } for i in totals.line_breakdown],
            "subtotal_base": totals.subtotal_base,
            "total": totals.total_after_discounts,
            "saved": saved_amount,
            "exterior_tier": totals.discount_tier_used_exterior,
            "interior_tier": totals.discount_tier_used_interior,
            "flags": totals.flags_summary,
        })

    except Exception as e:
        # Log full traceback to server logs and return a readable error to client
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------------------------------
# API: Export PDF
# -----------------------------------------------------------------------------
@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    """
    Request JSON:
      {
        "client_name": "Acme Co",
        "items": [{ "type_display": "Exterior", "variant": "Full Wrap", "months": 4, "qty": 2 }, ...],
        "discount_choice": "None" | "Agency 10%" | "PSA 10%",
        "upfront_selected": true | false
      }
    Returns: application/pdf as attachment
    """
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

        discount_choice = data.get("discount_choice", "None")
        upfront_selected = bool(data.get("upfront_selected", False))

        # Run the same calculator used by /quote
        result = compute_quote(items_spec, discount_choice, upfront_selected)

        # Build PDF bytes and stream to client
        pdf_bytes = build_quote_pdf_bytes(client_name, result)
        buffer = BytesIO(pdf_bytes)

        # Safe filename
        safe_client = "".join(c for c in client_name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"RTS_Quote_{safe_client or 'Client'}.pdf"

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        return jsonify({"error": str(e)}), 400


# -----------------------------------------------------------------------------
# Entrypoint (local)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # For local testing
    app.run(host="0.0.0.0", port=5000, debug=True)
