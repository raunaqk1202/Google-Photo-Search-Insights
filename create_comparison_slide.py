"""
Generate a Canva-compatible .pptx comparison slide (1920×1080 px).
Design mirrors the reference: Google-colored corner blocks, clean white background,
color-coded rows with a comparison table.

Font: Calibri (MS), minimum size 22pt.
"""

import collections
import collections.abc
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Presentation setup ──────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width = Inches(20)       # 1920 px at 96 DPI
prs.slide_height = Inches(11.25)   # 1080 px at 96 DPI

slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank layout

# ── Color palette ────────────────────────────────────────────────────────────
BLUE        = RGBColor(0x42, 0x85, 0xF4)
RED         = RGBColor(0xEA, 0x43, 0x35)
YELLOW      = RGBColor(0xFB, 0xBC, 0x05)
GREEN       = RGBColor(0x34, 0xA8, 0x53)
DARK_GRAY   = RGBColor(0x20, 0x21, 0x24)
MID_GRAY    = RGBColor(0x5F, 0x63, 0x68)
LIGHT_GRAY  = RGBColor(0xF1, 0xF3, 0xF4)
MUTED_GRAY  = RGBColor(0xDA, 0xDC, 0xE0)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
BG_COLOR    = RGBColor(0xFE, 0xFE, 0xFE)

# Row accent colors (alternating Google palette)
ROW_COLORS = [BLUE, RED, YELLOW, GREEN, BLUE]
ROW_BG_TINTS = [
    RGBColor(0xE8, 0xF0, 0xFE),   # light blue
    RGBColor(0xFC, 0xE8, 0xE6),   # light red
    RGBColor(0xFE, 0xF7, 0xE0),   # light yellow
    RGBColor(0xE6, 0xF4, 0xEA),   # light green
    RGBColor(0xE8, 0xF0, 0xFE),   # light blue
]

# ── Background ───────────────────────────────────────────────────────────────
bg = slide.background
fill = bg.fill
fill.solid()
fill.fore_color.rgb = BG_COLOR

# ── Helper functions ─────────────────────────────────────────────────────────

def add_square(slide, left, top, size, color):
    """Add a decorative square."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, size, size)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def add_textbox(slide, text, left, top, width, height,
                font_size=22, bold=False, color=DARK_GRAY,
                alignment=PP_ALIGN.LEFT, font_name='Calibri',
                v_anchor=MSO_ANCHOR.TOP):
    """Add a simple text box."""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = alignment
    p.font.size = Pt(font_size)
    p.font.name = font_name
    p.font.bold = bold
    p.font.color.rgb = color
    return txBox


def add_rich_cell(slide, left, top, width, height, bg_color,
                  heading, heading_color, body, body_color=DARK_GRAY,
                  heading_size=24, body_size=22):
    """Add a rounded box with heading + body text (multi-paragraph)."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    shape.line.fill.background()

    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.2)
    tf.margin_right = Inches(0.2)
    tf.margin_top = Inches(0.15)
    tf.margin_bottom = Inches(0.1)

    # Heading
    p1 = tf.paragraphs[0]
    p1.text = heading
    p1.font.size = Pt(heading_size)
    p1.font.name = 'Calibri'
    p1.font.bold = True
    p1.font.color.rgb = heading_color

    # Body
    p2 = tf.add_paragraph()
    p2.text = body
    p2.font.size = Pt(body_size)
    p2.font.name = 'Calibri'
    p2.font.bold = False
    p2.font.color.rgb = body_color
    p2.space_before = Pt(6)

    return shape


# ══════════════════════════════════════════════════════════════════════════════
# DECORATIVE CORNER SQUARES  (matches reference image)
# ══════════════════════════════════════════════════════════════════════════════

sq = Inches(0.7)

# Top-left cluster
add_square(slide, Inches(0.65), Inches(0), sq, BLUE)
add_square(slide, Inches(0),    Inches(0.65), sq, RED)
add_square(slide, Inches(0.65), Inches(1.35), sq, YELLOW)

# Top-right cluster (muted grays + green accent)
rx = Inches(17.1)
add_square(slide, rx,              Inches(0.3), Inches(0.55), MUTED_GRAY)
add_square(slide, rx + Inches(0.7), Inches(0.3), Inches(0.55), MUTED_GRAY)
add_square(slide, rx + Inches(1.4), Inches(0.3), Inches(0.55), MUTED_GRAY)
add_square(slide, rx + Inches(0.35), Inches(0.9), Inches(0.55), MUTED_GRAY)
add_square(slide, rx + Inches(1.05), Inches(0.9), Inches(0.55), MUTED_GRAY)
add_square(slide, rx + Inches(1.75), Inches(0.9), Inches(0.55), GREEN)

# ══════════════════════════════════════════════════════════════════════════════
# TITLE & SUBTITLE
# ══════════════════════════════════════════════════════════════════════════════

add_textbox(
    slide,
    "User Research vs. AI Discovery\nEngine: Key Comparisons",
    Inches(1.8), Inches(0.3), Inches(14), Inches(1.5),
    font_size=44, bold=True, color=DARK_GRAY
)

add_textbox(
    slide,
    "Validating qualitative survey insights (n=31) against\n"
    "1,982 scraped reviews analyzed by the AI discovery engine",
    Inches(1.8), Inches(1.75), Inches(14), Inches(0.9),
    font_size=24, bold=False, color=MID_GRAY
)

# ══════════════════════════════════════════════════════════════════════════════
# TABLE HEADER ROW
# ══════════════════════════════════════════════════════════════════════════════

table_x = Inches(1.2)
col_left_w = Inches(0.6)     # colored sidebar
col_topic_w = Inches(3.0)    # topic column
col_survey_w = Inches(6.5)   # user research column
col_engine_w = Inches(6.8)   # AI engine column
row_h = Inches(1.32)
header_h = Inches(0.7)
header_y = Inches(2.95)
gap = Inches(0.08)

# Header background
header_bg = slide.shapes.add_shape(
    MSO_SHAPE.ROUNDED_RECTANGLE,
    table_x, header_y,
    col_left_w + col_topic_w + col_survey_w + col_engine_w + gap * 3,
    header_h
)
header_bg.fill.solid()
header_bg.fill.fore_color.rgb = DARK_GRAY
header_bg.line.fill.background()

# Header labels
header_items = [
    ("", table_x, col_left_w),
    ("Insight Area", table_x + col_left_w + gap, col_topic_w),
    ("📋  User Research Survey (n=31)", table_x + col_left_w + col_topic_w + gap * 2, col_survey_w),
    ("🤖  AI Discovery Engine (1,982 reviews)", table_x + col_left_w + col_topic_w + col_survey_w + gap * 3, col_engine_w),
]
for text, x, w in header_items:
    if not text:
        continue
    tb = add_textbox(slide, text, x, header_y, w, header_h,
                     font_size=24, bold=True, color=WHITE,
                     alignment=PP_ALIGN.CENTER)
    tb.text_frame.paragraphs[0].font.name = 'Calibri'

# ══════════════════════════════════════════════════════════════════════════════
# TABLE DATA ROWS — real figures from both sources
# ══════════════════════════════════════════════════════════════════════════════

rows_data = [
    {
        "topic": "Search Failure\nRate",
        "survey": "61.3% (19/31) experienced complete initial search failure—unrelated photos, near-misses, or zero results",
        "engine": "Result Ranking Failure scored 61.9/100; Metadata Dependency scored 68.9/100 — top 2 ranked opportunities across 507 classified reviews",
    },
    {
        "topic": "Document\nSearch",
        "survey": "57.1% (4/7) of document searches returned completely unrelated photos; 0% yielded accurate top-ranked results",
        "engine": "OCR Indexing for Receipts & Documents identified as a distinct failure mode from 1,982 scraped reviews across 5 channels",
    },
    {
        "topic": "Person &\nGroup Photos",
        "survey": "50.0% (4/8) received related people but not the specific photo—precision issues in facial indexing",
        "engine": "Person Ambiguity scored 54.5/100 (Reach: 3.4/5, User Pain: 3.6/5); faces obscured or system mis-tagged",
    },
    {
        "topic": "Memory\nAnchors",
        "survey": "Top recall cues: Location 54.8%, Document Content 32.3%, Date/Time 29.0%, Event Name 29.0%",
        "engine": "Context Loss scored 54.8/100; Temporal Uncertainty & Memory Failure captured as separate failure modes from user verbatims",
    },
    {
        "topic": "Recovery &\nAbandonment",
        "survey": "52.6% (10/19) abandoned search for manual browsing; 31.6% (6/19) total abandonment—never found photo",
        "engine": "Search Strategy Failure scored 62.8/100 (User Pain: 3.8/5); Query Translation Failure & Vocabulary Mismatch also surfaced",
    },
]

start_y = header_y + header_h + Inches(0.12)

for i, row in enumerate(rows_data):
    y = start_y + i * (row_h + Inches(0.1))
    color = ROW_COLORS[i]
    tint = ROW_BG_TINTS[i]

    # Colored sidebar
    sidebar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, table_x, y, col_left_w, row_h
    )
    sidebar.fill.solid()
    sidebar.fill.fore_color.rgb = color
    sidebar.line.fill.background()

    # Topic cell
    add_rich_cell(
        slide,
        table_x + col_left_w + gap, y,
        col_topic_w, row_h,
        bg_color=tint,
        heading=row["topic"],
        heading_color=color,
        heading_size=24,
        body="",
        body_size=22,
    )

    # Survey cell
    survey_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        table_x + col_left_w + col_topic_w + gap * 2, y,
        col_survey_w, row_h
    )
    survey_shape.fill.solid()
    survey_shape.fill.fore_color.rgb = WHITE
    survey_shape.line.color.rgb = LIGHT_GRAY
    survey_shape.line.width = Pt(1)

    stf = survey_shape.text_frame
    stf.word_wrap = True
    stf.margin_left = Inches(0.2)
    stf.margin_right = Inches(0.15)
    stf.margin_top = Inches(0.12)
    sp = stf.paragraphs[0]
    sp.text = row["survey"]
    sp.font.size = Pt(22)
    sp.font.name = 'Calibri'
    sp.font.color.rgb = DARK_GRAY

    # Engine cell
    engine_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        table_x + col_left_w + col_topic_w + col_survey_w + gap * 3, y,
        col_engine_w, row_h
    )
    engine_shape.fill.solid()
    engine_shape.fill.fore_color.rgb = WHITE
    engine_shape.line.color.rgb = LIGHT_GRAY
    engine_shape.line.width = Pt(1)

    etf = engine_shape.text_frame
    etf.word_wrap = True
    etf.margin_left = Inches(0.2)
    etf.margin_right = Inches(0.15)
    etf.margin_top = Inches(0.12)
    ep = etf.paragraphs[0]
    ep.text = row["engine"]
    ep.font.size = Pt(22)
    ep.font.name = 'Calibri'
    ep.font.color.rgb = DARK_GRAY


# ══════════════════════════════════════════════════════════════════════════════
# FOOTER — Sources
# ══════════════════════════════════════════════════════════════════════════════

add_textbox(
    slide,
    "Sources: User Research Survey (n=31 respondents)  •  AI Discovery Engine (1,982 reviews from Play Store, YouTube, Reddit, App Store, Google Support)  •  507 classified reviews scored via LLM",
    Inches(1.2), Inches(10.6), Inches(17.5), Inches(0.5),
    font_size=18, bold=False, color=MID_GRAY
)


# ══════════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════════

output_path = '/Users/raunaqkaicker/Documents/Google photos AI discovery engine/User_Research_vs_Discovery_Engine.pptx'
prs.save(output_path)
print(f"✅ Slide saved to: {output_path}")
