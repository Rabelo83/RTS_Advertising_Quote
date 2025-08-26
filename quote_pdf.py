# quote_pdf.py

from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def build_quote_pdf_bytes(client_name: str, result) -> bytes:
    buf = BytesIO()
    _build_story_into_doc(buf, client_name, result)
    return buf.getvalue()


def save_quote_pdf_file(filepath: str, client_name: str, result) -> None:
    _build_story_into_doc(filepath, client_name, result)


def _build_story_into_doc(target, client_name: str, result) -> None:
    styles = getSampleStyleSheet()

    # Headings
    title = ParagraphStyle(
        "RTSTitle",
        parent=styles["Title"],
        alignment=1,  # center
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

    # Story
    story = []
    story.append(Paragraph("City of Gainesville", title))
    story.append(Paragraph("RTS Quote for Advertising", subtitle))

    story.append(Paragraph(f"<b>Client:</b> {escape_text(client_name)}", normal))
    story.append(Spacer(1, 10))

    # Items table (expects result.items -> List[LineItem])
    data = [["Type", "Product/Size", "Code", "Months", "Qty", "Unit Price", "Line Total"]]
    for it in getattr(result, "items", []):
        data.append([
            escape_text(it.type_display),
            escape_text(it.product),
            escape_text(it.code),
            str(it.months),
            str(it.qty),
            f"${it.unit_price:,.2f}",
            f"${it.line_total:,.2f}",
        ])

    tbl = Table(data, hAlign="LEFT", colWidths=[80, 140, 70, 55, 40, 90, 90])
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

    # Totals block (uses result.subtotal_base, result.total, result.saved)
    subtotal = getattr(result, "subtotal_base", 0.0)
    total    = getattr(result, "total", 0.0)
    saved    = getattr(result, "saved", round(subtotal - total, 2))

    story.append(Paragraph(f"<b>Subtotal:</b> ${subtotal:,.2f}", normal))
    story.append(Paragraph(f"<b>Total after discounts:</b> ${total:,.2f}", normal))
    story.append(Paragraph(f"<b>You saved:</b> ${saved:,.2f}", normal))
    story.append(Spacer(1, 8))

    # Transparency
    ext_tier = getattr(result, "exterior_tier", 0)
    int_tier = getattr(result, "interior_tier", 0)
    flags    = getattr(result, "flags_summary", "None")

    story.append(Paragraph(f"Exterior tier used: {ext_tier} (0=Base, 1=1st, 2=2nd, 3=3rd)", normal))
    story.append(Paragraph(f"Interior tier used: {int_tier} (0=Base, 1=1st)", normal))
    story.append(Paragraph(f"Flags applied: {escape_text(flags)}", normal))
    story.append(Spacer(1, 12))

    # ----- Footer callback (true bottom footer on every page) -----
    def footer_canvas(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        page_width, _ = LETTER

        line1 = ("Template reviewed and approved as to form and legality by the City Attorney's Office "
                 "on 05/22/2022; valid through 05/22/2023.")
        line2 = ("Station 5 - P.O Box 490 - Gainesville, FL 32627 - "
                 "Ph: 352-334-2600 - Fax: 352-334-3681 - www.go-rts.com")

        # Draw centered a bit above the bottom margin
        canvas.drawCentredString(page_width / 2.0, 42, line1)
        canvas.drawCentredString(page_width / 2.0, 30, line2)
        canvas.restoreState()

    # Build document with a larger bottom margin so the footer never overlaps
    doc = BaseDocTemplate(
        target,
        pagesize=LETTER,
        topMargin=36,
        bottomMargin=72,  # reserve space for footer
        leftMargin=36,
        rightMargin=36,
        title="RTS Quote",
    )

    # Content frame (slightly reduced height to give footer breathing room)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    doc.addPageTemplates(PageTemplate(id='page', frames=frame, onPage=footer_canvas))

    doc.build(story)


def escape_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
