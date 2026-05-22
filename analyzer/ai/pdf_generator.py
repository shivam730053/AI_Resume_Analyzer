"""
analyzer/ai/pdf_generator.py
 
Usage:
    from .ai.pdf_generator import generate_pdf_report
 
    pdf_buffer = generate_pdf_report(
        score='78',
        match_percentage='65',
        skills=['Python', 'SQL', ...],
        match_skills=['Python', ...],
        missing_skills=['Docker', ...],
        strengths=['Strong ML background', ...],
        weaknesses=['No cloud experience', ...],
    )
    # pdf_buffer is a BytesIO object ready to pass to HttpResponse
"""
 
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
 
# ── Brand palette ─────────────────────────────────────────────────────────────
PURPLE       = colors.HexColor("#534AB7")
PURPLE_DARK  = colors.HexColor("#3C3489")
PURPLE_LIGHT = colors.HexColor("#EEEDFE")
TEAL         = colors.HexColor("#1D9E75")
TEAL_LIGHT   = colors.HexColor("#E1F5EE")
CORAL        = colors.HexColor("#D85A30")
CORAL_LIGHT  = colors.HexColor("#FAECE7")
RED          = colors.HexColor("#E24B4A")
RED_LIGHT    = colors.HexColor("#FCEBEB")
GRAY_TEXT    = colors.HexColor("#6C757D")
BLACK        = colors.HexColor("#1A1A1A")
WHITE        = colors.white
 
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
USABLE = PAGE_W - 2 * MARGIN
 
 
# ── Style registry ────────────────────────────────────────────────────────────
 
def _build_styles():
    base = getSampleStyleSheet()
 
    def add(name, **kw):
        base.add(ParagraphStyle(name=name, **kw))
 
    add("BrandTitle",
        fontName="Helvetica-Bold", fontSize=22,
        textColor=PURPLE_DARK, spaceAfter=2, alignment=TA_LEFT)
 
    add("BrandSub",
        fontName="Helvetica", fontSize=9,
        textColor=GRAY_TEXT, spaceAfter=0, alignment=TA_LEFT)
 
    add("SectionHeading",
        fontName="Helvetica-Bold", fontSize=10,
        textColor=WHITE, spaceAfter=0, spaceBefore=0, alignment=TA_LEFT)
 
    add("Body",
        fontName="Helvetica", fontSize=9.5,
        textColor=BLACK, leading=14, spaceAfter=3)
 
    add("SkillBadge",
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=PURPLE_DARK, alignment=TA_CENTER)
 
    add("TableHeader",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, alignment=TA_CENTER)
 
    add("FooterStyle",
        fontName="Helvetica", fontSize=7.5,
        textColor=GRAY_TEXT, alignment=TA_CENTER)
 
    return base
 
 
# ── Reusable building blocks ──────────────────────────────────────────────────
 
def _section_header(label, color, styles):
    """Full-width colored pill heading."""
    tbl = Table(
        [[Paragraph(label.upper(), styles["SectionHeading"])]],
        colWidths=[USABLE],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    return tbl
 
 
def _kpi_cards(score, match_percentage, styles):
    """Two side-by-side score cards."""
    col = USABLE / 2 - 4
 
    def card(label, value, unit, bg, tc):
        lbl_style = ParagraphStyle("_kl", fontName="Helvetica-Bold",
                                   fontSize=8, textColor=tc, alignment=TA_CENTER)
        val_style = ParagraphStyle("_kv", fontName="Helvetica-Bold",
                                   fontSize=30, textColor=tc,
                                   alignment=TA_CENTER, leading=34)
        sub_style = ParagraphStyle("_ks", fontName="Helvetica",
                                   fontSize=8, textColor=tc, alignment=TA_CENTER)
        inner = Table(
            [[Paragraph(label, lbl_style)],
             [Paragraph(value, val_style)],
             [Paragraph(unit,  sub_style)]],
            colWidths=[col],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return inner
 
    score_card = card("RESUME SCORE", str(score), "out of 100", PURPLE_LIGHT, PURPLE_DARK)
    match_card  = card("JOB MATCH",   f"{match_percentage}%", "match rate", TEAL_LIGHT, TEAL)
 
    outer = Table([[score_card, match_card]], colWidths=[col, col])
    outer.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("COLPADDING",    (0, 0), (-1, -1), 8),
    ]))
    return outer
 
 
def _skills_badges(skills, styles):
    """Skills as a 4-column badge grid."""
    if not skills:
        return Paragraph("No skills detected.", styles["Body"])
 
    COLS = 4
    cw   = USABLE / COLS
 
    def badge(text):
        if not text:
            return ""
        p = Paragraph(text, styles["SkillBadge"])
        t = Table([[p]], colWidths=[cw - 10])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), PURPLE_LIGHT),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ]))
        return t
 
    rows = [skills[i:i+COLS] for i in range(0, len(skills), COLS)]
    # Pad last row so every row has exactly COLS cells
    while len(rows[-1]) < COLS:
        rows[-1].append("")
 
    tbl_data = [[badge(cell) for cell in row] for row in rows]
    tbl = Table(tbl_data, colWidths=[cw] * COLS, spaceBefore=4, spaceAfter=4)
    tbl.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl
 
 
def _matched_missing_table(match_skills, missing_skills, styles):
    """Side-by-side matched (teal) / missing (coral) table."""
    col = USABLE / 2
 
    cell_style = ParagraphStyle("_mc", fontName="Helvetica", fontSize=9,
                                textColor=BLACK, leading=13)
 
    def make_col(items):
        out = [[Paragraph(item, cell_style)] for item in items]
        return out or [[Paragraph("None", styles["Body"])]]
 
    matched_rows = make_col(match_skills)
    missing_rows = make_col(missing_skills)
 
    hdr = [
        Paragraph("Matched Skills", styles["TableHeader"]),
        Paragraph("Missing Skills", styles["TableHeader"]),
    ]
 
    max_r = max(len(matched_rows), len(missing_rows))
    empty = [Paragraph("", styles["Body"])]
    matched_rows += [empty] * (max_r - len(matched_rows))
    missing_rows += [empty] * (max_r - len(missing_rows))
 
    data = [hdr] + [[matched_rows[i][0], missing_rows[i][0]] for i in range(max_r)]
 
    tbl = Table(data, colWidths=[col, col], spaceBefore=4, spaceAfter=4)
    tbl.setStyle(TableStyle([
        # Headers
        ("BACKGROUND",     (0, 0), (0, 0), TEAL),
        ("BACKGROUND",     (1, 0), (1, 0), CORAL),
        ("TOPPADDING",     (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING",  (0, 0), (-1, 0), 8),
        # Body rows
        ("TOPPADDING",     (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 1), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 12),
        ("ROWBACKGROUNDS", (0, 1), (0, -1), [WHITE, TEAL_LIGHT]),
        ("ROWBACKGROUNDS", (1, 1), (1, -1), [WHITE, CORAL_LIGHT]),
        ("LINEAFTER",      (0, 0), (0, -1), 0.5, colors.HexColor("#E0DFDF")),
        ("BOX",            (0, 0), (-1, -1), 0.5, colors.HexColor("#E0DFDF")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tbl
 
 
def _bullet_list(items, dot_color, row_bg, styles):
    """Alternating-row bulleted list."""
    if not items:
        return Paragraph("None listed.", styles["Body"])
 
    dot_style = ParagraphStyle("_d", fontName="Helvetica-Bold", fontSize=12,
                               textColor=dot_color, alignment=TA_CENTER)
 
    rows = [
        [Paragraph("-", dot_style), Paragraph(item, styles["Body"])]
        for item in items
    ]
 
    tbl = Table(rows, colWidths=[14, USABLE - 14], spaceBefore=4, spaceAfter=4)
    tbl.setStyle(TableStyle([
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, row_bg]),
    ]))
    return tbl
 
 
def _logo_bar(styles):
    """Top logo + report label."""
    logo = Paragraph(
        '<b>ResumeAI</b>',
        ParagraphStyle("_logo", fontName="Helvetica-Bold", fontSize=16,
                       textColor=PURPLE, alignment=TA_LEFT),
    )
    tag = Paragraph(
        "Analysis Report",
        ParagraphStyle("_tag", fontName="Helvetica", fontSize=9,
                       textColor=GRAY_TEXT, alignment=TA_RIGHT),
    )
    tbl = Table([[logo, tag]], colWidths=[USABLE * 0.6, USABLE * 0.4])
    tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return tbl
 
 
# ── Public API ────────────────────────────────────────────────────────────────
 
def generate_pdf_report(
    score,
    match_percentage,
    skills,
    match_skills,
    missing_skills,
    strengths,
    weaknesses,
):
    """
    Build a styled PDF resume analysis report.
 
    All list parameters must be Python lists of strings.
    score and match_percentage can be str or int/float.
 
    Returns a BytesIO buffer — pass directly to HttpResponse.
    """
    # Ensure types are correct even if caller passes None
    skills         = skills         or []
    match_skills   = match_skills   or []
    missing_skills = missing_skills or []
    strengths      = strengths      or []
    weaknesses     = weaknesses     or []
    score          = str(score)          if score          is not None else "0"
    match_percentage = str(match_percentage) if match_percentage is not None else "0"
 
    buffer = BytesIO()
    styles = _build_styles()
 
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,  rightMargin=MARGIN,
        topMargin=MARGIN,   bottomMargin=MARGIN,
        title="Resume Analysis Report",
        author="ResumeAI",
    )
 
    story = []
 
    # Logo bar
    story.append(_logo_bar(styles))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=PURPLE_LIGHT,
        spaceBefore=6, spaceAfter=10,
    ))
 
    # Title
    story.append(Paragraph("Resume Analysis Report", styles["BrandTitle"]))
    
    story.append(Spacer(1, 12))
 
    # KPI cards
    story.append(_kpi_cards(score, match_percentage, styles))
    story.append(Spacer(1, 16))
 
    # Detected skills
    story.append(KeepTogether([
        _section_header("Detected Skills", PURPLE, styles),
        Spacer(1, 6),
        _skills_badges(skills, styles),
        Spacer(1, 14),
    ]))
 
    # Matched vs Missing
    story.append(KeepTogether([
        _section_header("Skills Breakdown", TEAL, styles),
        Spacer(1, 6),
        _matched_missing_table(match_skills, missing_skills, styles),
        Spacer(1, 14),
    ]))
 
    # Strengths
    story.append(KeepTogether([
        _section_header("Strengths", TEAL, styles),
        Spacer(1, 6),
        _bullet_list(strengths, TEAL, TEAL_LIGHT, styles),
        Spacer(1, 14),
    ]))
 
    # Weaknesses
    story.append(KeepTogether([
        _section_header("Areas to Improve", RED, styles),
        Spacer(1, 6),
        _bullet_list(weaknesses, RED, RED_LIGHT, styles),
        Spacer(1, 14),
    ]))
 
    # Footer
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=PURPLE_LIGHT, spaceAfter=5,
    ))
    story.append(Paragraph(
        "Generated by ResumeAI · This report is for personal use only.",
        styles["FooterStyle"],
    ))
 
    doc.build(story)
    buffer.seek(0)
    return buffer
 
