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
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

# ReportLab for PDF export
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm

LOGO_PATH = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')


def export_applications_to_excel(queryset):
    """Generate professional Excel spreadsheet of all registered members."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "KSFCTA Registered Members"
    ws.views.sheetView[0].showGridLines = True

    # Title Block
    ws.merge_cells('A1:O1')
    title_cell = ws['A1']
    title_cell.value = "KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION (KSFCTA)"
    title_cell.font = Font(name='Calibri', size=16, bold=True, color='FFFFFF')
    title_cell.fill = PatternFill(start_color='0F2B5C', end_color='0F2B5C', fill_type='solid')
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 36

    ws.merge_cells('A2:O2')
    sub_cell = ws['A2']
    sub_cell.value = f"Membership Campaign 2026 — Master Register (Generated: {datetime.now().strftime('%d-%b-%Y %I:%M %p')})"
    sub_cell.font = Font(name='Calibri', size=11, italic=True, color='FFFFFF')
    sub_cell.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    sub_cell.alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[2].height = 24

    # Column Headers
    headers = [
        "Sl No",
        "Application No",
        "Full Name",
        "Gender",
        "Date of Birth",
        "Mobile Number",
        "Email ID",
        "Institution / College",
        "Designation",
        "Department",
        "Category",
        "District",
        "PIN Code",
        "Membership Type",
        "Status"
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

    # Data Rows
    row_alt_fill = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
    row_white_fill = PatternFill(start_color='FFFFFF', end_color='FFFFFF', fill_type='solid')

    for idx, app in enumerate(queryset, 1):
        current_row = 4 + idx
        ws.row_dimensions[current_row].height = 22
        fill = row_alt_fill if idx % 2 == 0 else row_white_fill

        values = [
            idx,
            app.application_no,
            app.full_name,
            app.gender,
            app.dob.strftime('%d-%m-%Y') if app.dob else '',
            app.mobile,
            app.email,
            app.institution,
            app.designation,
            app.department,
            app.category,
            app.district,
            app.pincode,
            app.membership_type,
            app.status
        ]

        for col_num, val in enumerate(values, 1):
            cell = ws.cell(row=current_row, column=col_num)
            cell.value = val
            cell.fill = fill
            cell.border = border_thin
            cell.font = Font(name='Calibri', size=10)
            if col_num in [1, 2, 4, 5, 12, 13, 15]:
                cell.alignment = Alignment(horizontal='center', vertical='center')
            else:
                cell.alignment = Alignment(horizontal='left', vertical='center')

    # Auto-adjust column widths
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
    """Helper to set background color of a Word table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def export_single_application_docx(app):
    """Generate single filled official Word (.docx) document matching membership form.docx."""
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Header with Logo & Title
    header_table = doc.add_table(rows=1, cols=2)
    header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header_table.autofit = False

    col_logo = header_table.columns[0]
    col_text = header_table.columns[1]
    col_logo.width = Inches(1.2)
    col_text.width = Inches(5.8)

    # Logo
    cell_logo = header_table.cell(0, 0)
    if os.path.exists(LOGO_PATH):
        p_logo = cell_logo.paragraphs[0]
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.add_run().add_picture(LOGO_PATH, width=Inches(1.0))

    # Text
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

    r4 = p_title.add_run("Email: ksfcta@gmail.com, info.ksfcta@gmail.com | Contact: 9995514415")
    r4.font.size = Pt(8.5)
    r4.italic = True

    # Horizontal divider rule
    p_div = doc.add_paragraph()
    p_div.paragraph_format.space_before = Pt(4)
    p_div.paragraph_format.space_after = Pt(4)
    r_div = p_div.add_run("━" * 62)
    r_div.font.color.rgb = RGBColor(26, 86, 219)
    r_div.font.size = Pt(10)

    # Form Heading
    p_form = doc.add_paragraph()
    p_form.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_form.paragraph_format.space_before = Pt(2)
    p_form.paragraph_format.space_after = Pt(2)
    r_fh = p_form.add_run("MEMBERSHIP APPLICATION FORM – 2026")
    r_fh.bold = True
    r_fh.font.size = Pt(13)
    r_fh.underline = True

    # Application details row
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_after = Pt(8)
    r_appno = p_meta.add_run(f"Application No: {app.application_no}           ")
    r_appno.bold = True
    r_date = p_meta.add_run(f"Date: {app.created_at.strftime('%d / %m / %Y')}")
    r_date.bold = True

    # Table of form fields (11 points matching membership form.docx)
    fields = [
        ("1", "Name (in Block Letters):", app.full_name),
        ("2", "Gender:", app.gender),
        ("3", "Date of Birth:", app.dob.strftime('%d-%m-%Y') if app.dob else ''),
        ("4", "Mobile Number:", app.mobile),
        ("5", "Email ID:", app.email),
        ("6", "Name of Institution:", app.institution),
        ("7", "Designation:", app.designation),
        ("8", "Department:", app.department),
        ("9", "Category:", app.category),
        ("10", "Permanent Address & PIN:", f"{app.address}\nDistrict: {app.district}, PIN: {app.pincode}"),
        ("11", "Type of Membership:", app.membership_type),
    ]

    table = doc.add_table(rows=len(fields), cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    # Adjust widths
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

        # Subtle row styling
        if idx % 2 == 0:
            set_cell_background(c0, "F8FAFC")
            set_cell_background(c1, "F8FAFC")
            set_cell_background(c2, "F8FAFC")

    # Declaration Block
    p_dec_title = doc.add_paragraph()
    p_dec_title.paragraph_format.space_before = Pt(12)
    p_dec_title.paragraph_format.space_after = Pt(2)
    r_dt = p_dec_title.add_run("Declaration")
    r_dt.bold = True
    r_dt.font.size = Pt(11)

    p_dec = doc.add_paragraph()
    p_dec.paragraph_format.space_after = Pt(24)
    r_dec = p_dec.add_run(
        "I hereby declare that the information furnished above is true and correct to the best of my knowledge. "
        "I agree to abide by the Constitution, Rules and Regulations of the Self Financing College Teachers Association & Staff Union."
    )
    r_dec.font.size = Pt(9.5)
    r_dec.italic = True

    # Signature Row
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig = p_sig.add_run(f"Digitally Confirmed / Signature of Applicant\n({app.full_name})")
    r_sig.bold = True
    r_sig.font.size = Pt(10)

    # For Office Use Only Section
    p_off = doc.add_paragraph()
    p_off.paragraph_format.space_before = Pt(10)
    p_off.paragraph_format.space_after = Pt(4)
    r_off = p_off.add_run("For Office Use Only")
    r_off.bold = True
    r_off.underline = True
    r_off.font.size = Pt(11)

    off_table = doc.add_table(rows=4, cols=2)
    off_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    off_rows = [
        ("Application Received on:", app.created_at.strftime('%d / %m / %Y')),
        ("Membership Fee Received:", app.membership_fee or "₹ __________________"),
        ("Receipt No.:", app.receipt_no or "________________________"),
        ("Membership No. & Approved By:", f"{app.membership_no or '_________________'} / {app.approved_by or '_________________'}")
    ]
    for i, (k, v) in enumerate(off_rows):
        row = off_table.rows[i]
        row.cells[0].width = Inches(2.6)
        row.cells[1].width = Inches(4.4)
        row.cells[0].text = k
        row.cells[0].paragraphs[0].runs[0].bold = True
        row.cells[1].text = v

    # Output to response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    safe_name = "".join(c for c in app.full_name if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"KSFCTA_Form_{app.application_no}_{safe_name}.docx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    doc.save(response)
    return response


def export_single_application_pdf(app):
    """Generate official PDF printable Membership Application Form matching official layout."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'MainTitle',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0F2B5C'),
        alignment=1
    )
    sub_style = ParagraphStyle(
        'SubTitle',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155'),
        alignment=1
    )
    form_hdr_style = ParagraphStyle(
        'FormHdr',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )
    cell_lbl_style = ParagraphStyle(
        'CellLbl',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    cell_val_style = ParagraphStyle(
        'CellVal',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1E293B')
    )

    story = []

    # Header with Logo & Association details
    header_data = []
    if os.path.exists(LOGO_PATH):
        logo_img = RLImage(LOGO_PATH, width=1.1*inch, height=1.1*inch)
    else:
        logo_img = Paragraph("<b>KSFCTA</b>", title_style)

    header_text = Paragraph(
        "<b>KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION</b><br/>"
        "<font size=8><b>(Reg. No.: TVM/TC/425/2023)</b></font><br/>"
        "<font size=8>KSFCTA Mandir, Vanchiyoor, Thiruvananthapuram – 695035, Kerala</font><br/>"
        "<font size=7.5 color='#475569'>Email: ksfcta@gmail.com, info.ksfcta@gmail.com | Phone: 9995514415</font>",
        ParagraphStyle('HdrTxt', fontName='Helvetica', leading=13, alignment=0)
    )

    hdr_table = Table([[logo_img, header_text]], colWidths=[1.3*inch, 5.7*inch])
    hdr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 6))

    # Divider bar
    div_table = Table([['']], colWidths=[7.0*inch], rowHeights=[2])
    div_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A56DB')),
    ]))
    story.append(div_table)
    story.append(Spacer(1, 8))

    # Form Title
    story.append(Paragraph("MEMBERSHIP APPLICATION FORM – 2026", form_hdr_style))
    story.append(Spacer(1, 6))

    # Metadata Row (App No & Date)
    meta_table = Table([
        [
            Paragraph(f"<b>Application No:</b> <font color='#1A56DB'>{app.application_no}</font>", cell_val_style),
            Paragraph(f"<b>Status:</b> <b>{app.status}</b>", cell_val_style),
            Paragraph(f"<b>Date:</b> {app.created_at.strftime('%d-%m-%Y')}", cell_val_style)
        ]
    ], colWidths=[2.8*inch, 2.0*inch, 2.2*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F1F5F9')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # Data Table matching 11 points
    fields = [
        ("1", "Name (in Block Letters)", app.full_name),
        ("2", "Gender", app.gender),
        ("3", "Date of Birth", app.dob.strftime('%d-%m-%Y') if app.dob else ''),
        ("4", "Mobile Number", app.mobile),
        ("5", "Email ID", app.email),
        ("6", "Name of Institution", app.institution),
        ("7", "Designation", app.designation),
        ("8", "Department", app.department),
        ("9", "Category", app.category),
        ("10", "Permanent Address", f"{app.address}<br/><b>District:</b> {app.district} &nbsp;|&nbsp; <b>PIN:</b> {app.pincode}"),
        ("11", "Type of Membership", app.membership_type),
    ]

    table_data = []
    for sl, label, val in fields:
        table_data.append([
            Paragraph(f"<b>{sl}</b>", cell_lbl_style),
            Paragraph(f"<b>{label}</b>", cell_lbl_style),
            Paragraph(str(val or ''), cell_val_style)
        ])

    data_table = Table(table_data, colWidths=[0.4*inch, 2.3*inch, 4.3*inch])
    data_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F8FAFC')]),
    ]))
    story.append(data_table)
    story.append(Spacer(1, 8))

    # Declaration Box
    dec_text = (
        "<b>Declaration:</b><br/>"
        "<i>I hereby declare that the information furnished above is true and correct to the best of my knowledge. "
        "I agree to abide by the Constitution, Rules and Regulations of the Self Financing College Teachers Association & Staff Union.</i>"
    )
    dec_table = Table([[Paragraph(dec_text, cell_val_style)]], colWidths=[7.0*inch])
    dec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#93C5FD')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(dec_table)
    story.append(Spacer(1, 10))

    # Signature Row
    sig_table = Table([
        [
            Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d-%m-%Y')}", cell_val_style),
            Paragraph(f"<b>Signature of Applicant:</b><br/><font color='#2563EB'>[Digitally Verified - {app.full_name}]</font>", cell_val_style)
        ]
    ], colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 10))

    # For Office Use Only Section
    off_data = [
        [
            Paragraph("<b>FOR OFFICE USE ONLY</b>", form_hdr_style),
            Paragraph("", cell_val_style)
        ],
        [
            Paragraph(f"<b>Application Received on:</b> {app.created_at.strftime('%d-%m-%Y')}", cell_val_style),
            Paragraph(f"<b>Membership Fee Received:</b> {app.membership_fee or '₹ ....................'}", cell_val_style)
        ],
        [
            Paragraph(f"<b>Receipt No:</b> {app.receipt_no or '..........................'}", cell_val_style),
            Paragraph(f"<b>Membership No:</b> {app.membership_no or '..........................'}", cell_val_style)
        ],
        [
            Paragraph(f"<b>Approved By:</b> {app.approved_by or 'State President / General Secretary'}", cell_val_style),
            Paragraph(f"<b>Office Seal & Date:</b> ..........................", cell_val_style)
        ]
    ]
    off_table = Table(off_data, colWidths=[3.5*inch, 3.5*inch])
    off_table.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#E2E8F0')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('GRID', (0,1), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(off_table)

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    safe_name = "".join(c for c in app.full_name if c.isalnum() or c in (' ', '_')).rstrip()
    response['Content-Disposition'] = f'attachment; filename="KSFCTA_Form_{app.application_no}_{safe_name}.pdf"'
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
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1E293B')
    )

    story = []
    story.append(Paragraph("<b>KERALA SELF FINANCING COLLEGE TEACHERS’ ASSOCIATION (KSFCTA)</b>", title_style))
    story.append(Paragraph(f"<font size=9>Membership Campaign 2026 — Master Summary Report (Total: {queryset.count()})</font>", title_style))
    story.append(Spacer(1, 8))

    headers = [
        Paragraph("Sl", th_style),
        Paragraph("App No", th_style),
        Paragraph("Name", th_style),
        Paragraph("Gender", th_style),
        Paragraph("Mobile", th_style),
        Paragraph("Institution", th_style),
        Paragraph("Designation", th_style),
        Paragraph("District", th_style),
        Paragraph("Type", th_style),
        Paragraph("Status", th_style)
    ]
    rows = [headers]

    for idx, app in enumerate(queryset, 1):
        rows.append([
            Paragraph(str(idx), td_style),
            Paragraph(app.application_no, td_style),
            Paragraph(app.full_name, td_style),
            Paragraph(app.gender, td_style),
            Paragraph(app.mobile, td_style),
            Paragraph(app.institution[:25], td_style),
            Paragraph(app.designation[:20], td_style),
            Paragraph(app.district, td_style),
            Paragraph(app.membership_type.replace(' Membership', ''), td_style),
            Paragraph(app.status, td_style),
        ])

    table = Table(rows, colWidths=[
        0.3*inch, 1.0*inch, 1.2*inch, 0.5*inch, 0.8*inch, 1.4*inch, 0.9*inch, 0.8*inch, 0.6*inch, 0.5*inch
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
