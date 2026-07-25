"""
FinVox — Sample PDF Invoice Generator
Generates a realistic Sri Lankan B2B IT Consulting invoice for RAG testing.
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "sample", "sample_invoice.pdf")

# ── Invoice Data ─────────────────────────────────────────────────────────────
INVOICE = {
    "number":       "INV-2026-0842",
    "date":         "15 July 2026",
    "due_date":     "29 July 2026",
    "po_number":    "PO-SAMPATH-2026-114",
}

VENDOR = {
    "name":     "LankaTech Solutions (Pvt) Ltd",
    "address":  "Level 4, 42 Sir Mohamed Macan Markar Mawatha,\nColombo 3, Western Province, Sri Lanka",
    "phone":    "+94 11 234 5678",
    "email":    "billing@lankatech.lk",
    "vat_reg":  "VAT Reg: 135-798-2045 SVT",
    "br_no":    "BR No: PV 108972",
}

CLIENT = {
    "name":     "Sampath Bank PLC",
    "attn":     "Mr. Nuwan Perera, Head of IT Procurement",
    "address":  "110 Sir James Peiris Mawatha,\nColombo 2, Sri Lanka",
}

LINE_ITEMS = [
    # (Description, Qty, Unit, Unit Price LKR)
    ("Cloud Infrastructure Monitoring & Management\n  AWS / Azure environment oversight — July 2026", 1, "Month", 185000.00),
    ("Custom ERP Module Development\n  Accounts Payable automation module (Sprint 3 & 4)", 80, "Hours", 3500.00),
    ("Cybersecurity Audit & Penetration Testing\n  Quarterly security assessment — Q3 2026", 1, "Service", 145000.00),
    ("On-Site Support & Maintenance\n  2 Senior Engineers × 3 days", 6, "Man-days", 18500.00),
    ("Software License Procurement (Reseller)\n  Microsoft Azure Reserved Instances — 12 months", 1, "License", 220000.00),
    ("Technical Documentation & Training\n  Staff training (10 participants, 2 sessions)", 1, "Package", 65000.00),
]

BANK = {
    "bank":     "Hatton National Bank PLC",
    "branch":   "Colombo 3 — Union Place Branch",
    "account":  "011-010-234-567-001",
    "swift":    "HBLILKLX",
}

NOTES = [
    "Payment is due within 14 days of the invoice date.",
    "Late payments will attract a 2% monthly interest charge.",
    "All prices are exclusive of VAT (18%) unless stated.",
    "Please quote Invoice Number INV-2026-0842 in all payment references.",
]

# ── Build PDF ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(OUTPUT, pagesize=A4,
                        leftMargin=15*mm, rightMargin=15*mm,
                        topMargin=15*mm, bottomMargin=15*mm)

styles = getSampleStyleSheet()
BLUE  = colors.HexColor("#1A3C6E")
LGRAY = colors.HexColor("#F5F7FA")
MGRAY = colors.HexColor("#D0D7E3")
WHITE = colors.white
BLACK = colors.black

h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=22, textColor=WHITE, spaceAfter=2)
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, textColor=BLUE, spaceAfter=4)
normal = ParagraphStyle("normal", fontName="Helvetica", fontSize=9, textColor=BLACK, leading=13)
small  = ParagraphStyle("small",  fontName="Helvetica", fontSize=8, textColor=colors.grey, leading=11)
bold9  = ParagraphStyle("bold9",  fontName="Helvetica-Bold", fontSize=9, textColor=BLACK)
right9 = ParagraphStyle("right9", fontName="Helvetica", fontSize=9, textColor=BLACK, alignment=TA_RIGHT)
rightB = ParagraphStyle("rightB", fontName="Helvetica-Bold", fontSize=10, textColor=BLUE, alignment=TA_RIGHT)

story = []

# ── HEADER BANNER ─────────────────────────────────────────────────────────────
header_data = [[
    Paragraph(VENDOR["name"], h1),
    Paragraph("TAX INVOICE", ParagraphStyle("inv", fontName="Helvetica-Bold",
              fontSize=26, textColor=WHITE, alignment=TA_RIGHT)),
]]
header_tbl = Table(header_data, colWidths=[110*mm, 70*mm])
header_tbl.setStyle(TableStyle([
    ("BACKGROUND",   (0,0), (-1,-1), BLUE),
    ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING",   (0,0), (-1,-1), 10),
    ("BOTTOMPADDING",(0,0), (-1,-1), 10),
]))
story.append(header_tbl)
story.append(Spacer(1, 4*mm))

# ── VENDOR INFO + INVOICE META ────────────────────────────────────────────────
vendor_text = (f"{VENDOR['address']}<br/>"
               f"Tel: {VENDOR['phone']}  |  {VENDOR['email']}<br/>"
               f"{VENDOR['vat_reg']}  |  {VENDOR['br_no']}")

meta_rows = [
    ["Invoice No:",  INVOICE["number"]],
    ["Invoice Date:", INVOICE["date"]],
    ["Due Date:",    INVOICE["due_date"]],
    ["PO Reference:", INVOICE["po_number"]],
]
meta_data = [[Paragraph(r[0], small), Paragraph(r[1], bold9)] for r in meta_rows]
meta_tbl = Table(meta_data, colWidths=[28*mm, 52*mm])
meta_tbl.setStyle(TableStyle([
    ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
    ("LEFTPADDING",   (0,0), (-1,-1), 5),
    ("RIGHTPADDING",  (0,0), (-1,-1), 5),
    ("TOPPADDING",    (0,0), (-1,-1), 3),
    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ("GRID",          (0,0), (-1,-1), 0.3, MGRAY),
    ("TEXTCOLOR",     (0,0), (0,-1), colors.grey),
]))

info_data = [[
    Paragraph(vendor_text, small),
    meta_tbl,
]]
info_tbl = Table(info_data, colWidths=[110*mm, 70*mm])
info_tbl.setStyle(TableStyle([
    ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING",  (0,0), (-1,-1), 0),
    ("RIGHTPADDING", (0,0), (-1,-1), 0),
]))
story.append(info_tbl)
story.append(Spacer(1, 4*mm))

# ── BILL TO ───────────────────────────────────────────────────────────────────
bill_header = Table([["BILL TO"]], colWidths=[180*mm])
bill_header.setStyle(TableStyle([
    ("BACKGROUND",   (0,0), (-1,-1), BLUE),
    ("TEXTCOLOR",    (0,0), (-1,-1), WHITE),
    ("FONT",         (0,0), (-1,-1), "Helvetica-Bold", 9),
    ("LEFTPADDING",  (0,0), (-1,-1), 6),
    ("TOPPADDING",   (0,0), (-1,-1), 4),
    ("BOTTOMPADDING",(0,0), (-1,-1), 4),
]))
story.append(bill_header)

bill_data = [[
    Paragraph(CLIENT["name"], bold9),
    Paragraph(CLIENT["attn"], normal),
    Paragraph(CLIENT["address"], small),
]]
bill_tbl = Table([bill_data], colWidths=[55*mm, 70*mm, 55*mm])
bill_tbl.setStyle(TableStyle([
    ("BACKGROUND",   (0,0), (-1,-1), LGRAY),
    ("LEFTPADDING",  (0,0), (-1,-1), 6),
    ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ("TOPPADDING",   (0,0), (-1,-1), 5),
    ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ("VALIGN",       (0,0), (-1,-1), "TOP"),
]))
story.append(bill_tbl)
story.append(Spacer(1, 5*mm))

# ── LINE ITEMS TABLE ──────────────────────────────────────────────────────────
col_headers = ["#", "Description", "Qty", "Unit", "Unit Price (LKR)", "Amount (LKR)"]
tbl_data = [col_headers]

subtotal = 0
for i, (desc, qty, unit, price) in enumerate(LINE_ITEMS, 1):
    amount = qty * price
    subtotal += amount
    tbl_data.append([
        str(i),
        Paragraph(desc.replace("\n", "<br/>"), small),
        str(qty),
        unit,
        f"{price:,.2f}",
        f"{amount:,.2f}",
    ])

vat_rate    = 0.18
vat_amount  = subtotal * vat_rate
total       = subtotal + vat_amount
withholding = subtotal * 0.05   # 5% WHT (common in Sri Lanka B2B)
net_payable = total - withholding

# Totals section
tbl_data += [
    ["", "", "", "", Paragraph("Sub-Total:", right9),         f"{subtotal:,.2f}"],
    ["", "", "", "", Paragraph("VAT (18%):", right9),         f"{vat_amount:,.2f}"],
    ["", "", "", "", Paragraph("Withholding Tax (5%):", right9), f"({withholding:,.2f})"],
    ["", "", "", "", Paragraph("NET PAYABLE (LKR):", rightB), Paragraph(f"{net_payable:,.2f}", rightB)],
]

items_tbl = Table(tbl_data, colWidths=[8*mm, 82*mm, 10*mm, 16*mm, 32*mm, 32*mm])
items_tbl.setStyle(TableStyle([
    # Header
    ("BACKGROUND",    (0,0), (-1,0), BLUE),
    ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
    ("FONT",          (0,0), (-1,0), "Helvetica-Bold", 8),
    ("ALIGN",         (0,0), (-1,0), "CENTER"),
    # Body
    ("FONT",          (0,1), (-1,-5), "Helvetica", 8),
    ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ("ALIGN",         (2,1), (2,-1), "CENTER"),
    ("ALIGN",         (4,1), (5,-1), "RIGHT"),
    ("ROWBACKGROUNDS",(0,1), (-1,-5), [WHITE, LGRAY]),
    # Grid
    ("GRID",          (0,0), (-1,-5), 0.3, MGRAY),
    ("LINEABOVE",     (0,-4), (-1,-4), 0.5, MGRAY),
    ("LINEABOVE",     (0,-1), (-1,-1), 1.5, BLUE),
    # Totals bg
    ("BACKGROUND",    (0,-1), (-1,-1), LGRAY),
    ("FONT",          (4,-4), (-1,-1), "Helvetica-Bold", 9),
    ("TOPPADDING",    (0,0), (-1,-1), 4),
    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ("LEFTPADDING",   (0,0), (-1,-1), 4),
    ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    # Span empty cells in totals
    ("SPAN",          (0,-4), (3,-4)),
    ("SPAN",          (0,-3), (3,-3)),
    ("SPAN",          (0,-2), (3,-2)),
    ("SPAN",          (0,-1), (3,-1)),
]))
story.append(items_tbl)
story.append(Spacer(1, 5*mm))

# ── BANK DETAILS + NOTES ──────────────────────────────────────────────────────
bank_text = (f"<b>Bank:</b> {BANK['bank']}<br/>"
             f"<b>Branch:</b> {BANK['branch']}<br/>"
             f"<b>Account No:</b> {BANK['account']}<br/>"
             f"<b>SWIFT:</b> {BANK['swift']}")

notes_text = "<br/>".join(f"• {n}" for n in NOTES)

footer_data = [[
    [Paragraph("PAYMENT DETAILS", h2), Paragraph(bank_text, small)],
    [Paragraph("TERMS & CONDITIONS", h2), Paragraph(notes_text, small)],
]]
footer_tbl = Table(footer_data, colWidths=[90*mm, 90*mm])
footer_tbl.setStyle(TableStyle([
    ("BACKGROUND",   (0,0), (-1,-1), LGRAY),
    ("VALIGN",       (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING",  (0,0), (-1,-1), 8),
    ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ("TOPPADDING",   (0,0), (-1,-1), 6),
    ("BOTTOMPADDING",(0,0), (-1,-1), 6),
    ("LINEAFTER",    (0,0), (0,-1), 0.5, MGRAY),
    ("BOX",          (0,0), (-1,-1), 0.5, MGRAY),
]))
story.append(footer_tbl)
story.append(Spacer(1, 4*mm))

# ── SIGNATURE BLOCK ───────────────────────────────────────────────────────────
story.append(HRFlowable(width="100%", thickness=1, color=BLUE))
story.append(Spacer(1, 3*mm))
sig_data = [[
    Paragraph("Authorized Signature: ____________________________", small),
    Paragraph("For and on behalf of <b>LankaTech Solutions (Pvt) Ltd</b>", small),
    Paragraph("This is a computer-generated invoice.", small),
]]
sig_tbl = Table([sig_data], colWidths=[65*mm, 75*mm, 40*mm])
sig_tbl.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
story.append(sig_tbl)

# ── BUILD ─────────────────────────────────────────────────────────────────────
doc.build(story)
print(f"[OK] Invoice PDF generated: '{OUTPUT}'")
print(f"     Subtotal   : LKR {subtotal:,.2f}")
print(f"     VAT (18%)  : LKR {vat_amount:,.2f}")
print(f"     WHT  (5%)  : LKR ({withholding:,.2f})")
print(f"     Net Payable: LKR {net_payable:,.2f}")
print(f"     Due Date   : {INVOICE['due_date']}")
