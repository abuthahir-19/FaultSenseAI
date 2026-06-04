"""
Generates SYSTEM_OVERVIEW.svg
Box design matches ARCHITECTURE.html exactly:
  • Tier containers  — white bg + shadow + coloured header + number badge
  • Component rows   — left 5-px coloured strip, emoji, bold name, muted desc
  • UI-mode chips    — centred icon + name card (like .um in HTML)
Run: python generate_overview_diagram.py
"""
import os, html as _html

OUT  = os.path.join(os.path.dirname(__file__), "SYSTEM_OVERVIEW.svg")
W, H = 1260, 930
FONT = "'Segoe UI', -apple-system, 'Inter', sans-serif"

def xe(s): return _html.escape(str(s))

# ── Exact Prodapt palette ─────────────────────────────────────────────────────
NAVY   = "#1B2A4A";  ORANGE = "#F26B43";  BLUE   = "#1B6EC2"
GREEN  = "#147A40";  VIOLET = "#6B21A8";  TEAL   = "#0D7E6D"
AMBER  = "#B45309";  RED    = "#B91C1C";  INDIGO = "#4338CA"
WHITE  = "#FFFFFF";  LIGHT  = "#F8FAFC";  DARK   = "#1E293B"
MUTED  = "#64748B";  BORDER = "#CBD5E1"

LT = { NAVY:LIGHT,   ORANGE:"#FFF7ED", BLUE:"#EBF5FF",
       GREEN:"#EDFD F4".replace(" ",""),  VIOLET:"#F5F3FF",
       TEAL:"#ECFDF5", AMBER:"#FFFBEB", RED:"#FEF2F2",
       INDIGO:"#EEF2FF" }

parts = []

# ── SVG open ──────────────────────────────────────────────────────────────────
parts.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     xmlns="http://www.w3.org/2000/svg"
     style="font-family:{FONT}; background:{LIGHT}">
<title>FaultSense AI — Complete System Overview</title>""")

# ── Defs ──────────────────────────────────────────────────────────────────────
arrow_cols = [(MUTED,"an"),(BLUE,"aq"),(VIOLET,"ad"),(GREEN,"ag"),
              (AMBER,"ar"),(TEAL,"at"),(INDIGO,"ai"),(RED,"ae"),(ORANGE,"ao")]
d = ["<defs>"]
for col, mid in arrow_cols:
    d.append(f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" '
             f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
             f'<path d="M1 2 L8 5 L1 8" fill="none" stroke="{col}" '
             f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
             f'</marker>')
d.append('<filter id="sh" x="-4%" y="-4%" width="108%" height="112%">'
         '<feDropShadow dx="0" dy="2" stdDeviation="5" '
         'flood-color="#0F172A" flood-opacity="0.09"/></filter>')
d.append('<filter id="sm" x="-5%" y="-5%" width="110%" height="115%">'
         '<feDropShadow dx="0" dy="1" stdDeviation="3" '
         'flood-color="#0F172A" flood-opacity="0.07"/></filter>')
d.append("</defs>")
parts.append("\n".join(d))

# ── Background ────────────────────────────────────────────────────────────────
parts.append(f'<rect width="{W}" height="{H}" fill="{LIGHT}"/>')
parts.append(f'<defs><pattern id="dg" x="0" y="0" width="28" height="28" '
             f'patternUnits="userSpaceOnUse">'
             f'<circle cx="14" cy="14" r="1" fill="{BORDER}" opacity="0.4"/>'
             f'</pattern></defs>'
             f'<rect width="{W}" height="{H}" fill="url(#dg)"/>')


# ═════════════════════════════════════════════════════════════════════════════
# SVG PRIMITIVES
# ═════════════════════════════════════════════════════════════════════════════
def R(x,y,w,h,fill,stroke=None,sw=1.5,rx=10,filt=""):
    f   = f' filter="url(#{filt})"' if filt else ""
    st  = f'stroke="{stroke}" stroke-width="{sw}"' if stroke else 'stroke="none"'
    parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                 f'rx="{rx}" fill="{fill}" {st}{f}/>')

def T(x,y,s,size=11,fill=DARK,weight="normal",anchor="middle",italic=False):
    fs = "italic" if italic else "normal"
    parts.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
                 f'font-weight="{weight}" font-style="{fs}" fill="{fill}" '
                 f'text-anchor="{anchor}" dominant-baseline="central">{xe(s)}</text>')

def line(x1,y1,x2,y2,col,sw=2,dash="",marker=""):
    da = f'stroke-dasharray="{dash}"' if dash else ""
    me = f'marker-end="url(#{marker})"' if marker else ""
    parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                 f'stroke="{col}" stroke-width="{sw}" {da} {me} stroke-linecap="round"/>')

def path_arrow(d_str,col,sw=2,dash="",marker=""):
    da = f'stroke-dasharray="{dash}"' if dash else ""
    me = f'marker-end="url(#{marker})"' if marker else ""
    parts.append(f'<path d="{d_str}" fill="none" stroke="{col}" '
                 f'stroke-width="{sw}" {da} {me} '
                 f'stroke-linecap="round" stroke-linejoin="round"/>')


# ═════════════════════════════════════════════════════════════════════════════
# BOX DESIGN HELPERS  (matching ARCHITECTURE.html exactly)
# ═════════════════════════════════════════════════════════════════════════════

def tier_container(x, y, w, h, acc):
    """White outer container with shadow — like .tier"""
    R(x, y, w, h, WHITE, acc, sw=1.5, rx=12, filt="sh")

def tier_header(x, y, w, icon, label, acc, num=None):
    """
    Full-width coloured header band — like .tier-hd
    Number badge circle on the left if num is provided.
    """
    # Rounded top, flat bottom
    R(x, y,   w, 38, acc, rx=12, sw=0)
    R(x, y+26, w, 12, acc, rx=0,  sw=0)   # cover rounded bottom corners
    if num:
        bx = x + 19
        parts.append(f'<circle cx="{bx}" cy="{y+19}" r="13" '
                     f'fill="{WHITE}" opacity="0.22"/>')
        T(bx, y+19, str(num), size=11, fill=WHITE, weight="800")
        T(x + 40, y+19, f"{icon}  {label}",
          size=11, fill=WHITE, weight="700", anchor="start")
    else:
        T(x + w//2, y+19, f"{icon}  {label}",
          size=12, fill=WHITE, weight="800")

def tier_body_bg(x, y, w, h, acc):
    """Light-accent body background — like .tier-bd"""
    lt = LT.get(acc, LIGHT)
    R(x, y, w, h, lt, rx=0, sw=0)
    # Close the container (cover bottom with rounded rect)
    R(x, y+h-12, w, 12, lt, rx=0, sw=0)


def comp_row(x, y, w, h, icon, name, desc, acc, badge_num=None):
    """
    Horizontal component row — matches .cr / .lg-node in ARCHITECTURE.html
      • Light tinted background + 1 px solid border
      • Left 5-px coloured strip (accent colour)
      • Optional numbered circle badge (for pipeline agents)
      • Emoji icon (15 px, no circle wrapper)
      • Bold name in accent colour
      • Small muted description
    """
    lt = LT.get(acc, LIGHT)
    R(x, y, w, h, lt, acc, sw=1, rx=8)          # card bg
    R(x, y, 5, h, acc, rx=0, sw=0)               # left strip

    if badge_num is not None:
        # Numbered circle badge (like .nn in HTML)
        bx = x + 19
        parts.append(f'<circle cx="{bx}" cy="{y+h//2}" r="11" fill="{acc}"/>')
        T(bx, y+h//2, str(badge_num), size=9, fill=WHITE, weight="800")
        ico_x = x + 37
    else:
        ico_x = x + 18

    T(ico_x, y+h//2, icon, size=15, anchor="middle")     # emoji (no circle)
    tx = ico_x + 22
    T(tx, y+h//2-9, name, size=9.5, fill=acc, weight="700", anchor="start")
    T(tx, y+h//2+8, desc, size=8,   fill=MUTED,            anchor="start")


def ui_mode_chip(x, y, w, h, icon, label, sub, acc):
    """
    Centred mode chip — matches .um in ARCHITECTURE.html
    Icon (centred, 16 px) + bold label + small muted sub
    """
    lt = LT.get(acc, LIGHT)
    R(x, y, w, h, lt, acc, sw=1, rx=8)
    T(x+w//2, y+h//2-13, icon,  size=16, anchor="middle")
    T(x+w//2, y+h//2+ 3, label, size=9,  fill=acc, weight="700")
    T(x+w//2, y+h//2+16, sub,   size=7.5,fill=MUTED)


def arrow_pill(x, y, label, col):
    """Small pill label on an arrow."""
    lw = len(label)*6.2 + 14
    R(x-lw//2, y-10, lw, 19, WHITE, col, sw=0.9, rx=9)
    T(x, y, label, size=8, fill=col, weight="600")


# ═════════════════════════════════════════════════════════════════════════════
# TITLE BANNER
# ═════════════════════════════════════════════════════════════════════════════
R(0, 0, W, 66, NAVY, rx=0)
R(0, 61, W, 5, ORANGE, rx=0)
T(W//2, 25, "FaultSense AI — Complete System Overview",
  size=22, fill=WHITE, weight="800")
T(W//2, 50,
  "Data Ingestion  ·  Quick Search  ·  Deep Analysis  —  All Three Flows Connected",
  size=10.5, fill="#94A3B8")


# ═════════════════════════════════════════════════════════════════════════════
# INTERFACE LAYER
# ═════════════════════════════════════════════════════════════════════════════
# ── User pill ────────────────────────────────────────────────────────────────
UY = 82
R(W//2-145, UY, 290, 44, WHITE, BORDER, sw=1.5, rx=22, filt="sm")
T(W//2, UY+22, "👤  User / NOC Engineer", size=12, fill=DARK, weight="700")

line(W//2, UY+44, W//2, UY+56, MUTED, sw=1.8, marker="an")

# ── Frontend tier container ───────────────────────────────────────────────────
FY = UY+58
FW, FH = W-80, 103
tier_container(40, FY, FW, FH, BLUE)
tier_header(40, FY, FW, "⚛", "React Frontend", BLUE, num="①")
tier_body_bg(40, FY+38, FW, FH-38, BLUE)

# 4 UI-mode chips inside frontend (matches .um design)
modes = [
    ("🔎", "Query Mode",     "Search incidents",    BLUE),
    ("🧠", "Deep Analysis",   "AI agent pipeline",   VIOLET),
    ("📊", "Analytics",       "Trends & forecasts",  TEAL),
    ("📋", "Evaluation",      "Quality metrics",     ORANGE),
]
chip_w, chip_h = 262, 50
total_cw = len(modes)*chip_w + (len(modes)-1)*10
cx0 = W//2 - total_cw//2
for icon, label, sub, acc in modes:
    ui_mode_chip(cx0, FY+44, chip_w, chip_h, icon, label, sub, acc)
    cx0 += chip_w + 10

line(W//2, FY+FH, W//2, FY+FH+12, MUTED, sw=1.8, marker="an")

# ── Backend tier container ────────────────────────────────────────────────────
BY = FY+FH+14
BW, BH = W-80, 52
tier_container(40, BY, BW, BH, GREEN)
tier_header(40, BY, BW, "⚡", "FastAPI Backend", GREEN, num="②")

BB = BY+BH


# ═════════════════════════════════════════════════════════════════════════════
# FORK ARROWS
# Bus-style: one vertical drop → horizontal bus → two vertical drops
# Keeps arrows clear of all boxes.
# ═════════════════════════════════════════════════════════════════════════════
QS_X, QS_W = 40,  348
DA_X, DA_W = 412, 410
EX_X, EX_W = 846, 374

QS_CX = QS_X + QS_W//2    # 214
DA_CX = DA_X + DA_W//2    # 617
COL_Y = BB + 42

BUS_Y = BB + 20
R(W//2-1, BB, 2, BUS_Y-BB+2, MUTED, rx=0, sw=0)
R(QS_CX-1, BUS_Y-1, DA_CX-QS_CX+2, 2, BORDER, rx=0, sw=0)
line(QS_CX, BUS_Y, QS_CX, COL_Y-4, BLUE,   sw=2, marker="aq")
line(DA_CX, BUS_Y, DA_CX, COL_Y-4, VIOLET, sw=2, marker="ad")
arrow_pill(QS_CX-2, BUS_Y-12, "Quick Search",   BLUE)
arrow_pill(DA_CX+2, BUS_Y-12, "Deep Analysis",  VIOLET)


# ═════════════════════════════════════════════════════════════════════════════
# QUICK SEARCH TIER
# ═════════════════════════════════════════════════════════════════════════════
QS_STEPS = [
    ("🛡", "Guardrail Check",    "Validates safety & relevance",      ORANGE),
    ("🔍", "Hybrid Search",      "Finds similar incidents via RAG",    BLUE),
    ("💡", "Quick Root Cause",   "AI reads results, suggests cause",   AMBER),
    ("📋", "Incident Results",   "Ranked cards with severity scores",  GREEN),
]
ROW_H, ROW_GAP = 44, 6
QS_BODY_H = len(QS_STEPS)*(ROW_H+ROW_GAP) - ROW_GAP
QS_TH = 38 + 10 + QS_BODY_H + 10     # header + top pad + rows + bottom pad
QS_TIER_H = QS_TH

tier_container(QS_X, COL_Y, QS_W, QS_TIER_H, BLUE)
tier_header(QS_X, COL_Y, QS_W, "🔎", "Quick Search", BLUE)
tier_body_bg(QS_X, COL_Y+38, QS_W, QS_TIER_H-38, BLUE)

cy = COL_Y + 38 + 10
qs_row_cy = {}
for icon, name, desc, acc in QS_STEPS:
    comp_row(QS_X+8, cy, QS_W-16, ROW_H, icon, name, desc, acc)
    qs_row_cy[name] = cy + ROW_H//2
    if (icon,name,desc,acc) != QS_STEPS[-1]:
        line(QS_CX, cy+ROW_H, QS_CX, cy+ROW_H+ROW_GAP, BLUE, sw=1.5, marker="aq")
    cy += ROW_H + ROW_GAP

QS_BOT = COL_Y + QS_TIER_H


# ═════════════════════════════════════════════════════════════════════════════
# DEEP ANALYSIS TIER
# ═════════════════════════════════════════════════════════════════════════════
DA_STEPS = [
    (1, "🛡", "Guardrail Check",      "Validates safety & relevance",          ORANGE),
    (2, "📚", "Retrieve Incidents",    "Finds related alarms — Hybrid RAG",      BLUE),
    (3, "🔗", "Correlate Alarms",      "Groups by region & technology",          AMBER),
    (4, "🎯", "Root Cause + Impact",   "GPT-4o explains why & who is affected",  VIOLET),
    (5, "✅", "Recommendations",       "Step-by-step fix guide (5 categories)",  GREEN),
    (6, "📊", "RAG Evaluation",        "Auto quality score for this analysis",   TEAL),
]
DA_ROW_H, DA_ROW_GAP = 46, 6
DA_BODY_H = len(DA_STEPS)*(DA_ROW_H+DA_ROW_GAP) - DA_ROW_GAP
DA_TH = 38 + 10 + DA_BODY_H + 10

tier_container(DA_X, COL_Y, DA_W, DA_TH, VIOLET)
tier_header(DA_X, COL_Y, DA_W, "🧠", "Deep Analysis — 5-Node AI Pipeline", VIOLET)
tier_body_bg(DA_X, COL_Y+38, DA_W, DA_TH-38, VIOLET)

cy = COL_Y + 38 + 10
da_row_cy = {}
for num, icon, name, desc, acc in DA_STEPS:
    comp_row(DA_X+8, cy, DA_W-16, DA_ROW_H, icon, name, desc, acc,
             badge_num=num)
    da_row_cy[name] = cy + DA_ROW_H//2
    if num < len(DA_STEPS):
        line(DA_CX, cy+DA_ROW_H, DA_CX, cy+DA_ROW_H+DA_ROW_GAP,
             VIOLET, sw=1.5, marker="ad")
    cy += DA_ROW_H + DA_ROW_GAP

DA_BOT = COL_Y + DA_TH


# ═════════════════════════════════════════════════════════════════════════════
# EXTERNAL SERVICES TIER
# ═════════════════════════════════════════════════════════════════════════════
EX_STEPS = [
    ("🧠", "OpenAI API",    "GPT-4o  ·  text-embedding-3-small",     INDIGO),
    ("📊", "LangSmith",     "Agent trace  ·  token counts  ·  latency", TEAL),
    ("📋", "DeepEval",      "Faithfulness  ·  Relevancy  ·  Precision", RED),
]
EX_ROW_H, EX_ROW_GAP = 50, 8
EX_BODY_H = len(EX_STEPS)*(EX_ROW_H+EX_ROW_GAP) - EX_ROW_GAP
EX_TH = 38 + 10 + EX_BODY_H + 10

tier_container(EX_X, COL_Y, EX_W, EX_TH, NAVY)
tier_header(EX_X, COL_Y, EX_W, "🌐", "External Services", NAVY)
tier_body_bg(EX_X, COL_Y+38, EX_W, EX_TH-38, NAVY)

cy = COL_Y + 38 + 10
ex_row_cy = {}
for icon, name, desc, acc in EX_STEPS:
    comp_row(EX_X+8, cy, EX_W-16, EX_ROW_H, icon, name, desc, acc)
    ex_row_cy[name] = cy + EX_ROW_H//2
    cy += EX_ROW_H + EX_ROW_GAP


# ── Horizontal arrows  DA right edge → External (straight, no crossings) ─────
OAI_Y = ex_row_cy["OpenAI API"]
LS_Y  = ex_row_cy["LangSmith"]
DE_Y  = ex_row_cy["DeepEval"]

# Root Cause + Impact → OpenAI
RCA_Y = da_row_cy["Root Cause + Impact"]
line(DA_X+DA_W, RCA_Y, EX_X-2, OAI_Y, INDIGO, sw=1.5, dash="5 4", marker="ai")
arrow_pill((DA_X+DA_W+EX_X)//2, RCA_Y-12, "GPT-4o", INDIGO)

# DA pipeline → LangSmith
RET_Y = da_row_cy["Retrieve Incidents"]
line(DA_X+DA_W, RET_Y, EX_X-2, LS_Y, TEAL, sw=1.5, dash="5 4", marker="at")
arrow_pill((DA_X+DA_W+EX_X)//2, RET_Y-12, "Tracing", TEAL)

# RAG Evaluation → DeepEval
EVAL_Y = da_row_cy["RAG Evaluation"]
line(DA_X+DA_W, EVAL_Y, EX_X-2, DE_Y, RED, sw=1.8, marker="ae")
arrow_pill((DA_X+DA_W+EX_X)//2, EVAL_Y-12, "Evaluate", RED)


# ═════════════════════════════════════════════════════════════════════════════
# SHARED KNOWLEDGE BASE  (spans QS + DA columns, both arrow straight down)
# ═════════════════════════════════════════════════════════════════════════════
BOT_MAX = max(QS_BOT, DA_BOT)
KB_Y = BOT_MAX + 24
KB_W = DA_X + DA_W - QS_X
KB_H = 58

# Straight-down arrows from column centres into KB
line(QS_CX, QS_BOT, QS_CX, KB_Y-2, AMBER, sw=2, marker="ar")
line(DA_CX, DA_BOT, DA_CX, KB_Y-2, AMBER, sw=2, marker="ar")

tier_container(QS_X, KB_Y, KB_W, KB_H, AMBER)
tier_header(QS_X, KB_Y, KB_W, "📚", "Shared Knowledge Base", AMBER)
# Single-line body
T(QS_X+KB_W//2, KB_Y+48,
  "ChromaDB Vector Store  ·  BM25 Keyword Index  —  queried by Quick Search & Deep Analysis",
  size=9, fill=MUTED)


# ═════════════════════════════════════════════════════════════════════════════
# DATA INGESTION STRIP  (horizontal pipeline feeding the KB from below)
# ═════════════════════════════════════════════════════════════════════════════
DI_Y = KB_Y + KB_H + 36
DI_W = KB_W
DI_H = 62

# "feeds ↑" arrow
line(QS_X+DI_W//2, DI_Y-2, QS_X+DI_W//2, KB_Y+KB_H+2,
     GREEN, sw=2, marker="ag")
arrow_pill(QS_X+DI_W//2, DI_Y-18, "feeds ↑", GREEN)

tier_container(QS_X, DI_Y, DI_W, DI_H, GREEN)
tier_header(QS_X, DI_Y, DI_W, "📥", "Data Ingestion Pipeline", GREEN)

# 4 mini chips inside the strip (horizontal)
DI_ITEMS = [
    ("📄", "CSV File",         GREEN),
    ("🧮", "Embeddings (OpenAI)", AMBER),
    ("🗄", "Store — ChromaDB", VIOLET),
    ("🔍", "Build BM25 Index", TEAL),
]
mini_w = (DI_W - 20) // 4 - 8
mx = QS_X + 10
for icon, label, acc in DI_ITEMS:
    lt = LT.get(acc, LIGHT)
    R(mx, DI_Y+40, mini_w, 16, lt, acc, sw=0.8, rx=8)
    T(mx+mini_w//2, DI_Y+48, f"{icon}  {label}", size=8.5, fill=acc, weight="600")
    if label != DI_ITEMS[-1][1]:
        line(mx+mini_w+2, DI_Y+48, mx+mini_w+10, DI_Y+48, acc, sw=1.5)
    mx += mini_w + 10


# ═════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═════════════════════════════════════════════════════════════════════════════
FT_Y = DI_Y + DI_H + 18
R(0, FT_Y, W, H-FT_Y, NAVY, rx=0)
R(0, FT_Y, W, 3, ORANGE, rx=0)
T(W//2, FT_Y+(H-FT_Y)//2,
  "FaultSense AI  ·  Telecom Network Fault Intelligence  ·  2026",
  size=9, fill="#64748B")

parts.append("</svg>")
svg = "\n".join(parts)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"SVG: {OUT}  ({os.path.getsize(OUT):,} bytes)")
