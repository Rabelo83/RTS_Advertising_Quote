# quote_pdf.py

from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ----------------------------
# Public API
# ----------------------------

def build_quote_pdf_bytes(client_name: str, result) -> bytes:
    """
    Build the quote PDF in memory and return raw bytes.
    Use this in a Flask endpoint (send_file / BytesIO).
    """
    buf = BytesIO()
    _build_story_into_doc(buf, client_name, result)
    return buf.getvalue()

def save_quote_pdf_file(filepath: str, client_name: str, result) -> None:
    """
    Save the quote PDF to disk at `filepath`.
    Use this from your CLI flow if you want a local file.
    """
    _build_story_into_doc(filepath, client_name, result)  # accepts path or buffer


# ----------------------------
# Internal helpers
# ----------------------------

def _build_story_into_doc(target, client_name: str, result) -> None:
    """
    Build the PDF story and write it into `target`, which may be:
      - a filesystem path (str), or
      - a BytesIO buffer
    """
    styles = getSampleStyleSheet()

    # Tweak styles
    title = ParagraphStyle(
        "RTSTitle",
        parent=styles["Title"],
        alignment=1,  # centered
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )
    subtitle = ParagraphStyle(
        "RTSSubtitle",
        parent=styles["Title"],
        alignment=1,
        fontSize=14,
        leading=18,
        spaceAfter=16,
    )
    normal = styles["Normal"]

    # Story content
    story = []
    story.append(Paragraph("City of Gainesville", title))
    story.append(Paragraph("RTS Quote for Advertising", subtitle))

    story.append(Paragraph(f"<b>Client:</b> {escape_text(client_name)}", normal))
    story.append(Spacer(1, 10))

    # Items table
    data = [["Type", "Product/Size", "Code", "Months", "Qty", "Unit Price", "Line Total"]]
    for it in getattr(result, "line_breakdown", []):
        data.append([
            escape_text(it.type_display),
            escape_text(it.product),
            escape_text(it.code),
            str(it.months),
            str(it.qty),
            f"${it.unit_price:,.2f}",
            f"${it.line_total:,.2f}",
        ])

    tbl = Table(
        data,
        hAlign="LEFT",
        colWidths=[80, 140, 70, 55, 40, 90, 90]
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f3f7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),

        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))

    # Totals block
    subtotal = getattr(result, "subtotal_base", 0.0)
    total    = getattr(result, "total_after_discounts", 0.0)
    saved    = round(subtotal - total, 2)

    story.append(Paragraph(f"<b>Subtotal:</b> ${subtotal:,.2f}", normal))
    story.append(Paragraph(f"<b>Total after discounts:</b> ${total:,.2f}", normal))
    story.append(Paragraph(f"<b>You saved:</b> ${saved:,.2f}", normal))
    story.append(Spacer(1, 8))

    # Transparency (tiers + flags)
    ext_tier = getattr(result, "discount_tier_used_exterior", 0)
    int_tier = getattr(result, "discount_tier_used_interior", 0)
    flags    = getattr(result, "flags_summary", "None")

    story.append(Paragraph(f"Exterior tier used: {ext_tier} (0=Base, 1=1st, 2=2nd, 3=3rd)", normal))
    story.append(Paragraph(f"Interior tier used: {int_tier} (0=Base, 1=1st)", normal))
    story.append(Paragraph(f"Flags applied: {escape_text(flags)}", normal))
    story.append(Spacer(1, 20))

    # Footer (centered)
    footer = ParagraphStyle(
        "RTSFooter",
        parent=styles["Normal"],
        alignment=1,  # center
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#374151"),
    )
    footer_html = (
        "Template reviewed and approved as to form and legality by the City Attorney's Office "
        "on 05/22/2022; valid through 05/22/2023.<br/>"
        "Station 5 - P.O Box 490 - Gainesville, FL 32627 - "
        "Ph: 352-334-2600 - Fax: 352-334-3681 - www.go-rts.com"
    )
    story.append(Paragraph(footer_html, footer))

    # Build document
    doc = SimpleDocTemplate(
        target,
        pagesize=LETTER,
        topMargin=36, bottomMargin=36, leftMargin=36, rightMargin=36,
        title="RTS Quote",
    )
    doc.build(story)


def escape_text(s: str) -> str:
    """Minimal HTML escaping for Paragraph content."""
    if not isinstance(s, str):
        s = str(s)
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )
