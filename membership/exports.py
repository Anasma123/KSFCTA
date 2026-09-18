import os
import io
from datetime import datetime
from django.conf import settings
from django.http import HttpResponse

# OpenPyXL for Excel export
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Python-Docx for Word export
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

# ReportLab & PyPDF for PDF export & Letterhead merging
import pypdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def _find_asset_path(*relative_candidates):
    for rel in relative_candidates:
        for base in [settings.BASE_DIR, getattr(settings, 'STATIC_ROOT', None), *getattr(settings, 'STATICFILES_DIRS', [])]:
            if not base:
                continue
            cand = os.path.join(str(base), rel)
            if os.path.exists(cand):
                return cand
    return os.path.join(str(settings.BASE_DIR), relative_candidates[0])

LOGO_PATH = _find_asset_path('images/logo.png', 'static/images/logo.png', 'logo.png')
LETTERHEAD_PATH = _find_asset_path('templates/letterhead.pdf', 'static/templates/letterhead.pdf')


def export_applications_to_excel(queryset):
    """Generate professional Excel spreadsheet of all registered members with wings & payment status."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KSFCTA Registered Members"
    ws.views.sheetView[0].showGridLines = True

    # Title Block
    ws.merge_cells('A1:U1')
    title_cell = ws['A1']
    title_cell.value = "KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION (KSFCTA)"
    title_cell.font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    title_cell.fill = PatternFill(start_color='0F2B5C', end_color='0F2B5C', fill_type='solid')
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 36

    ws.merge_cells('A2:U2')
    sub_cell = ws['A2']
    sub_cell.value = f"Membership Campaign 2026 — Master Register (Generated: {datetime.now().strftime('%d-%b-%Y %I:%M %p')})"
    sub_cell.font = Font(name='Calibri', size=11, italic=True, color='FFFFFF')
    sub_cell.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    sub_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 24

    headers = [
        "Sl No",
        "Application No",
        "Membership ID",
        "Full Name",
        "Gender",
        "Date of Birth",
        "Mobile Number",
        "Email ID",
        "Wing",
        "Institution / College",
        "Designation",
        "Department",
        "Category",
        "District",
        "PIN Code",
        "Membership Type",
        "Transaction ID / UTR",
        "Payment Status",
        "Approval Status",
        "Rejection Reason",
        "Verified At"
    ]

    header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.row_dimensions[4].height = 28
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col_num)
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border_thin

    row_alt_fill = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
    row_white_fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

    for idx, app in enumerate(queryset, 1):
        current_row = 4 + idx
        ws.row_dimensions[current_row].height = 22
        fill = row_alt_fill if idx % 2 == 0 else row_white_fill

        values = [
            idx,
            app.application_no,
            app.membership_no or '',
            app.full_name,
            app.gender,
            app.dob.strftime('%d-%m-%Y') if app.dob else '',
            app.mobile,
            app.email,
            app.display_wing,
            app.institution,
            app.designation,
            app.department,
            app.category,
            app.district,
            app.pincode,
            app.membership_type,
            app.transaction_id or '',
            app.payment_status,
            app.status,
            app.rejection_reason or '',
            app.verified_at.strftime('%d-%m-%Y %I:%M %p') if app.verified_at else ''
        ]

        for col_num, val in enumerate(values, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = val
            cell.fill = fill
            cell.border = border_thin
            cell.font = Font(name='Calibri', size=10)
            if col_num in [1, 2, 3, 5, 6, 9, 14, 15, 16, 17, 18, 19, 21]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center')

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"KSFCTA_Members_Register_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def export_single_application_docx(app):
    """Generate filled Word (.docx) document matching membership form.docx with wings and fee details."""
    doc = Document()

    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    header_table = doc.add_table(rows=1, cols=2)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False
    header_table.columns[0].width = Inches(1.2)
    header_table.columns[1].width = Inches(5.8)

    cell_logo = header_table.cell(0, 0)
    if os.path.exists(LOGO_PATH):
        p_logo = cell_logo.paragraphs[0]
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.add_run().add_picture(LOGO_PATH, width=Inches(1.0))

    cell_text = header_table.cell(0, 1)
    p_title = cell_text.paragraphs[0]
    p_title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r1 = p_title.add_run("KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION\n")
    r1.bold = True
    r1.font.size = Pt(13)
    r1.font.color.rgb = RGBColor(15, 43, 92)

    r2 = p_title.add_run("(Reg. No.: TVM/TC/425/2023)\n")
    r2.font.size = Pt(9.5)
    r2.bold = True

    r3 = p_title.add_run("KSFCTA MANDIR, VANCHIYOOR, THIRUVANANTHAPURAM – 695035\n")
    r3.font.size = Pt(8.5)

    r4 = p_title.add_run("Contact: 9995514415")
    r4.font.size = Pt(8.5)
    r4.italic = True

    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(4)
    p_div.paragraph_format.space_after = Pt(4)
    r_div = p_div.add_run("━" * 62)
    r_div.font.color.rgb = RGBColor(26, 86, 219)

    p_form = doc.add_paragraph()
    p_form.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_form.paragraph_format.space_before = Pt(2)
    p_form.paragraph_format.space_after = Pt(2)
    r_fh = p_form.add_run("MEMBERSHIP APPLICATION FORM – 2026")
    r_fh.bold = True
    r_fh.font.size = Pt(13)
    r_fh.underline = True

    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(8)
    r_appno = p_meta.add_run(f"Application No: {app.application_no}           ")
    r_appno.bold = True
    r_date = p_meta.add_run(f"Date: {app.created_at.strftime('%d / %m / %Y')}")
    r_date.bold = True

    fields = [
        ("1", "Name (in Block Letters):", app.full_name),
        ("2", "Gender:", app.gender),
        ("3", "Date of Birth:", app.dob.strftime('%d-%m-%Y') if app.dob else ''),
        ("4", "Mobile Number:", app.mobile),
        ("5", "Email ID:", app.email),
        ("6", "Wing:", app.display_wing),
        ("7", "Name of Institution:", app.institution),
        ("8", "Designation:", app.designation),
        ("9", "Department:", app.department),
        ("10", "Category:", app.category),
        ("11", "Permanent Address & PIN:", f"{app.address}\nDistrict: {app.district}, PIN: {app.pincode}"),
        ("12", "Type of Membership:", app.membership_type),
        ("13", "Payment Details:", f"Fee: {app.membership_fee} | Status: {app.payment_status} | UTR: {app.transaction_id or 'N/A'}"),
    ]

    table = doc.add_table(rows=len(fields), cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    for row in table.rows:
        row.cells[0].width = Inches(0.4)
        row.cells[1].width = Inches(2.2)
        row.cells[2].width = Inches(4.4)

    for idx, (sl, label, val) in enumerate(fields):
        row = table.rows[idx]
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]

        c0.text = sl
        c0.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        c0.paragraphs[0].runs[0].bold = True

        c1.text = label
        c1.paragraphs[0].runs[0].bold = True

        c2.text = str(val or '')

        if idx % 2 == 0:
            set_cell_background(c0, "F8FAFC")
            set_cell_background(c1, "F8FAFC")
            set_cell_background(c2, "F8FAFC")

    p_dec_title = doc.add_paragraph()
    p_dec_title.paragraph_format.space_before = Pt(10)
    p_dec_title.paragraph_format.space_after = Pt(2)
    r_dt = p_dec_title.add_run("Declaration")
    r_dt.bold = True
    r_dt.font.size = Pt(11)

    p_dec = doc.add_paragraph()
    p_dec.paragraph_format.space_after = Pt(20)
    r_dec = p_dec.add_run(
        "I hereby declare that the information furnished above is true and correct to the best of my knowledge. "
        "I agree to abide by the Constitution, Rules and Regulations of the Self Financing College Teachers Association & Staff Union."
    )
    r_dec.font.size = Pt(9)
    r_dec.italic = True

    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig = p_sig.add_run(f"Signature / Digitally Verified\n({app.full_name})")
    r_sig.bold = True
    r_sig.font.size = Pt(10)

    p_off = doc.add_paragraph()
    p_off.paragraph_format.space_before = Pt(8)
    p_off.paragraph_format.space_after = Pt(4)
    r_off = p_off.add_run("For Office Use Only")
    r_off.bold = True
    r_off.underline = True

    off_table = doc.add_table(rows=4, cols=2)
    off_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    off_rows = [
        ("Application Received on:", app.created_at.strftime('%d / %m / %Y')),
        ("Membership Fee Received:", f"{app.membership_fee} (Status: {app.payment_status})"),
        ("Receipt No / UTR:", app.receipt_no or app.transaction_id or "________________________"),
        ("Membership No. & Approved By:", f"{app.membership_no or '_________________'} / {app.approved_by or '_________________'}")
    ]
    for i, (k, v) in enumerate(off_rows):
        row = off_table.rows[i]
        row.cells[0].width = Inches(2.6)
        row.cells[1].width = Inches(4.4)
        row.cells[0].text = k
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[1].text = v

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    safe_name = "".join(c for c in app.full_name if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"KSFCTA_Form_{app.application_no}_{safe_name}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response


def export_letterhead_certificate_pdf(app):
    """
    Generate Official Membership Certificate merged onto the official letterhead:
    brown and grey professional letterhead (4).pdf
    """
    packet = io.BytesIO()
    # A4 dimensions in points: 595.5 x 842.25
    can = canvas.Canvas(packet, pagesize=(595.5, 842.25))

    # Header is already pre-printed on the letterhead from Y=700 to 842!
    # Footer is already pre-printed on the letterhead from Y=0 to 90!
    # Printable area: X=48 to 548, Y=100 to 670.

    # 1. Certificate Title Banner
    can.setFont('Helvetica-Bold', 15)
    can.setFillColor(colors.HexColor('#0F2B5C'))
    # If standalone without letterhead PDF template, draw full header with exact logo
    if not (os.path.exists(LETTERHEAD_PATH)):
        if os.path.exists(LOGO_PATH):
            try:
                can.drawImage(LOGO_PATH, 55, 735, width=58, height=58, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        can.setFont('Helvetica-Bold', 12)
        can.setFillColor(colors.HexColor('#0F2B5C'))
        can.drawString(122, 770, "KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION")
        can.setFont('Helvetica-Bold', 8.5)
        can.setFillColor(colors.HexColor('#DC2626'))
        can.drawString(122, 756, "(Reg. No.: TVM/TC/425/2023)")
        can.setFont('Helvetica', 8)
        can.setFillColor(colors.HexColor('#475569'))
        can.drawString(122, 744, "KSFCTA Mandir, Vanchiyoor, Thiruvananthapuram – 695035 | Helpline: 9995514415")
        can.setStrokeColor(colors.HexColor('#0F2B5C'))
        can.setLineWidth(1.5)
        can.line(55, 728, 540, 728)
        can.setStrokeColor(colors.HexColor('#16A34A'))
        can.setLineWidth(1)
        can.line(55, 724, 540, 724)

    can.drawCentredString(297.75, 660, "MEMBERSHIP ADMISSION CERTIFICATE")

    can.setFont('Helvetica-Bold', 9)
    can.setFillColor(colors.HexColor('#1A56DB'))
    can.drawCentredString(297.75, 646, "KSFCTA STATE MEMBERSHIP CAMPAIGN 2026")

    # Thin decorative rule
    can.setStrokeColor(colors.HexColor('#CBD5E1'))
    can.setLineWidth(1)
    can.line(55, 636, 540, 636)

    # Reference & Date
    can.setFont('Helvetica-Bold', 8.5)
    can.setFillColor(colors.HexColor('#334155'))
    ref_no = app.membership_no if app.membership_no else f"KSFCTA/MEM/2026/{app.id:04d}"
    can.drawString(55, 622, f"Ref. No: {ref_no}")
    can.drawRightString(540, 622, f"Date of Issue: {datetime.now().strftime('%d-%m-%Y')}")

    # Salutation / To
    can.setFont('Helvetica-Bold', 9.5)
    can.setFillColor(colors.HexColor('#0F172A'))
    can.drawString(55, 598, "To,")
    can.drawString(55, 584, f"{app.full_name}")
    can.setFont('Helvetica', 9)
    can.setFillColor(colors.HexColor('#334155'))
    can.drawString(55, 571, f"{app.designation}, Department of {app.department}")
    can.drawString(55, 558, f"{app.institution}, {app.district} – {app.pincode}")

    # Certification statement
    can.setFont('Helvetica', 9.5)
    can.setFillColor(colors.HexColor('#1E293B'))
    statement_1 = (
        f"This is to certify that {app.full_name} has been officially registered, verified, and admitted"
    )
    statement_2 = (
        f"as an accredited member of the Kerala Self Financing College Teachers’ Association (KSFCTA)"
    )
    statement_3 = (
        f"under the patronage of KPCTA, following the democratic and progressive ideology of the Indian National Congress."
    )
    can.drawString(55, 532, statement_1)
    can.drawString(55, 519, statement_2)
    can.drawString(55, 506, statement_3)

    # Details Box (Official Membership Credential Card)
    can.setFillColor(colors.HexColor('#FFFFFF'))
    can.setStrokeColor(colors.HexColor('#93C5FD'))
    can.setLineWidth(1.2)
    can.roundRect(55, 235, 485, 240, 8, fill=1, stroke=1)

    # Card Top Banner (Navy Blue)
    can.setFillColor(colors.HexColor('#0F2B5C'))
    can.roundRect(55, 442, 485, 33, 6, fill=1, stroke=0)
    can.rect(55, 442, 485, 10, fill=1, stroke=0) # square bottom corners

    can.setFont('Helvetica-Bold', 11)
    can.setFillColor(colors.white)
    can.drawString(70, 454, "OFFICIAL MEMBERSHIP CREDENTIAL CARD")
    
    mem_display = app.membership_no if app.membership_no else f"KSFCTA-{app.created_at.year}-{app.id:04d}"
    can.setFont('Helvetica-Bold', 10)
    can.setFillColor(colors.HexColor('#FDE047')) # Gold accent
    can.drawRightString(525, 454, f"ID: {mem_display}")

    # Draw Member Passport Photo on the Right
    photo_x = 425
    photo_y = 295
    photo_w = 95
    photo_h = 125

    # Photo Frame Border
    can.setFillColor(colors.HexColor('#F8FAFC'))
    can.setStrokeColor(colors.HexColor('#93C5FD'))
    can.setLineWidth(1.5)
    can.roundRect(photo_x, photo_y, photo_w, photo_h, 4, fill=1, stroke=1)

    photo_drawn = False
    if app.photo:
        try:
            photo_path = app.photo.path if hasattr(app.photo, 'path') else str(app.photo)
            if os.path.exists(photo_path):
                can.drawImage(photo_path, photo_x + 2, photo_y + 2, width=photo_w - 4, height=photo_h - 4, preserveAspectRatio=True, anchor='c')
                photo_drawn = True
        except Exception:
            photo_drawn = False

    if not photo_drawn:
        can.setFont('Helvetica-Bold', 8)
        can.setFillColor(colors.HexColor('#94A3B8'))
        can.drawCentredString(photo_x + (photo_w / 2), photo_y + (photo_h / 2) + 6, "MEMBER")
        can.drawCentredString(photo_x + (photo_w / 2), photo_y + (photo_h / 2) - 6, "PHOTO")

    # Name label under photo
    can.setFont('Helvetica-Bold', 7.5)
    can.setFillColor(colors.HexColor('#0F2B5C'))
    short_name = app.full_name[:18]
    can.drawCentredString(photo_x + (photo_w / 2), photo_y - 12, short_name)

    # Member Details on the Left Side
    can.setFont('Helvetica-Bold', 9.5)
    can.setFillColor(colors.HexColor('#1E40AF'))
    can.drawString(70, 420, f"Unique ID:  {mem_display}")

    can.setFont('Helvetica-Bold', 9)
    can.setFillColor(colors.HexColor('#0F172A'))
    can.drawString(70, 402, f"Member Name:  {app.full_name}")

    can.setFont('Helvetica-Bold', 8.5)
    can.setFillColor(colors.HexColor('#334155'))
    can.drawString(70, 384, f"Designated Wing:  {app.display_wing}")

    can.setFont('Helvetica', 8.5)
    can.setFillColor(colors.HexColor('#334155'))
    can.drawString(70, 366, f"Designation:  {app.designation}")
    can.drawString(70, 348, f"Department:  {app.department}")
    can.drawString(70, 330, f"Institution:  {app.institution[:36]}")
    can.drawString(70, 312, f"District Chapter:  {app.district} (PIN: {app.pincode})")
    can.drawString(70, 294, f"Membership Type:  {app.membership_type} (Category: {app.category})")

    # Verification Status Pill on Card
    can.setFillColor(colors.HexColor('#ECFDF5'))
    can.setStrokeColor(colors.HexColor('#A7F3D0'))
    can.roundRect(70, 268, 230, 20, 3, fill=1, stroke=1)
    can.setFont('Helvetica-Bold', 8)
    can.setFillColor(colors.HexColor('#047857'))
    can.drawString(76, 274, "STATUS: VERIFIED & ACCREDITED MEMBER ✔")

    # Payment Confirmation Pill
    can.setFillColor(colors.HexColor('#EFF6FF'))
    can.setStrokeColor(colors.HexColor('#BFDBFE'))
    can.roundRect(310, 268, 105, 20, 3, fill=1, stroke=1)
    can.setFont('Helvetica-Bold', 7.5)
    can.setFillColor(colors.HexColor('#1D4ED8'))
    can.drawString(316, 274, f"Fee: {app.membership_fee} Paid")

    # Card Bottom Watermark Banner
    can.setStrokeColor(colors.HexColor('#E2E8F0'))
    can.setLineWidth(0.8)
    can.line(70, 256, 525, 256)
    can.setFont('Helvetica-Bold', 7.5)
    can.setFillColor(colors.HexColor('#64748B'))
    can.drawCentredString(297.75, 244, "Under Patronage of KPCTA & Democratic Ideology of Indian National Congress")

    # Slogan banner
    can.setFillColor(colors.HexColor('#EFF6FF'))
    can.setStrokeColor(colors.HexColor('#BFDBFE'))
    can.setLineWidth(1)
    can.roundRect(55, 172, 485, 42, 4, fill=1, stroke=1)
    can.setFont('Helvetica-Bold', 9.5)
    can.setFillColor(colors.HexColor('#1D4ED8'))
    can.drawCentredString(297.75, 196, "UNITED TEACHERS • STRONGER VOICE • BETTER FUTURE")
    can.setFont('Helvetica', 8)
    can.setFillColor(colors.HexColor('#475569'))
    can.drawCentredString(297.75, 182, "Kerala Self Financing College Teachers’ Association (Reg. No: TVM/TC/425/2023)")

    # Official Digital Verification Note
    can.setFont('Helvetica', 7.5)
    can.setFillColor(colors.HexColor('#64748B'))
    can.drawCentredString(297.75, 142, "This certificate is officially issued and digitally verified by the State Committee of KSFCTA.")
    can.drawCentredString(297.75, 130, "For official membership verification, contact: 9995514415 | KSFCTA Mandir, Vanchiyoor, Thiruvananthapuram – 695035")

    can.save()
    packet.seek(0)

    # Merge onto letterhead template
    if os.path.exists(LETTERHEAD_PATH):
        try:
            overlay_pdf = pypdf.PdfReader(packet)
            letterhead_pdf = pypdf.PdfReader(LETTERHEAD_PATH)
            writer = pypdf.PdfWriter()

            page = letterhead_pdf.pages[0]
            page.merge_page(overlay_pdf.pages[0])
            writer.add_page(page)

            out_buffer = io.BytesIO()
            writer.write(out_buffer)
            out_buffer.seek(0)
            pdf_bytes = out_buffer.getvalue()
        except Exception:
            pdf_bytes = packet.getvalue()
    else:
        pdf_bytes = packet.getvalue()

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    safe_name = "".join(c for c in app.full_name if c.isalnum() or c in (' ', '_')).rstrip()
    response['Content-Disposition'] = f'attachment; filename="KSFCTA_Certificate_{app.application_no}_{safe_name}.pdf"'
    return response


def export_summary_pdf(queryset):
    """Generate summary PDF report of all registered members."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MainTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0F2B5C'),
        alignment=1
    )
    th_style = ParagraphStyle(
        'TH',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'TD',
        fontName='Helvetica',
        fontSize=7,
        leading=9,
        textColor=colors.HexColor('#1E293B')
    )

    story = []
    if os.path.exists(LOGO_PATH):
        try:
            logo_img = RLImage(LOGO_PATH, width=42, height=42)
            logo_img.hAlign = 'CENTER'
            story.append(logo_img)
            story.append(Spacer(1, 4))
        except Exception:
            pass
    story.append(Paragraph("<b>KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION (KSFCTA)</b>", title_style))
    story.append(Paragraph(f"<font size=9>Membership Campaign 2026 — Master Summary Report (Total: {queryset.count()})</font>", title_style))
    story.append(Spacer(1, 8))

    headers = [
        Paragraph("Sl", th_style),
        Paragraph("App No", th_style),
        Paragraph("Name", th_style),
        Paragraph("Wing", th_style),
        Paragraph("Mobile", th_style),
        Paragraph("Institution", th_style),
        Paragraph("District", th_style),
        Paragraph("Payment", th_style),
        Paragraph("Status", th_style)
    ]
    rows = [headers]

    for idx, app in enumerate(queryset, 1):
        rows.append([
            Paragraph(str(idx), td_style),
            Paragraph(app.application_no, td_style),
            Paragraph(app.full_name, td_style),
            Paragraph(app.display_wing[:24], td_style),
            Paragraph(app.mobile, td_style),
            Paragraph(app.institution[:25], td_style),
            Paragraph(app.district, td_style),
            Paragraph(app.payment_status.replace(' Verification', ''), td_style),
            Paragraph(app.status.replace(' / Accepted', ''), td_style),
        ])

    table = Table(rows, colWidths=[
        0.3*inch, 1.0*inch, 1.2*inch, 1.1*inch, 0.8*inch, 1.4*inch, 0.8*inch, 0.7*inch, 0.7*inch
    ])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F2B5C')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
    ]))
    story.append(table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    filename = f"KSFCTA_Summary_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
