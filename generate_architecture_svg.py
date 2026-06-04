"""
Generates ARCHITECTURE_DIAGRAM.svg — presentation-friendly, dual-audience design.
Plain English labels for non-tech stakeholders; tech subtitles for engineers.
Run: python generate_architecture_svg.py
"""
import os, html as _html

def xe(s): return _html.escape(str(s), quote=False)

OUT = os.path.join(os.path.dirname(__file__), "ARCHITECTURE_DIAGRAM.svg")
W   = 1180

# ── Palette ───────────────────────────────────────────────────────────────────
BG     = "#F8FAFC"
BORDER = "#E2E8F0"
DARK   = "#0F172A"
MID    = "#334155"
FAINT  = "#94A3B8"
WHITE  = "#FFFFFF"

# Per-tier: (fill, accent, chip-fill, chip-text, sub-text)
FE  = dict(f="#EFF6FF", s="#2563EB", cf="#DBEAFE", ct="#1D4ED8", st="#3B82F6")
BE  = dict(f="#F0FDF4", s="#16A34A", cf="#DCFCE7", ct="#15803D", st="#22C55E")
RAG = dict(f="#FFFBEB", s="#D97706", cf="#FEF3C7", ct="#92400E", st="#F59E0B")
LG  = dict(f="#F5F3FF", s="#7C3AED", cf="#EDE9FE", ct="#5B21B6", st="#8B5CF6")
ST  = dict(f="#F1F5F9", s="#64748B", cf="#E2E8F0", ct="#334155", st="#64748B")
OAI = dict(f="#EEF2FF", s="#4F46E5", cf="#E0E7FF", ct="#3730A3", st="#6366F1")
LS  = dict(f="#ECFDF5", s="#059669", cf="#D1FAE5", ct="#065F46", st="#10B981")
DE  = dict(f="#FEF2F2", s="#DC2626", cf="#FEE2E2", ct="#991B1B", st="#EF4444")

FONT = "'Segoe UI', -apple-system, 'Inter', sans-serif"


# ── Primitives ────────────────────────────────────────────────────────────────
def rect(x, y, w, h, fill, stroke, rx=10, sw=1.5, filt=""):
    f = f' filter="{filt}"' if filt else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{f}/>')

def txt(x, y, content, size=11, fill=DARK, weight="normal",
        anchor="middle", family=FONT, italic=False):
    style = "italic" if italic else "normal"
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" font-style="{style}" fill="{fill}" '
            f'text-anchor="{anchor}" dominant-baseline="central">{xe(content)}</text>')

def line(x1, y1, x2, y2, stroke=FAINT, sw=1.8, dash="", marker="url(#arr)"):
    d = f'stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
            f'stroke-width="{sw}" {d} marker-end="{marker}" stroke-linecap="round"/>')

def path(d, stroke=FAINT, sw=1.8, dash="", fill="none", marker="url(#arr)"):
    da = f'stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'{da} marker-end="{marker}" stroke-linecap="round" stroke-linejoin="round"/>')

def flow_label(x, y, label, color=MID):
    pad = len(label) * 3.5 + 8
    return (f'<rect x="{x-pad}" y="{y-10}" width="{pad*2}" height="20" '
            f'rx="5" fill="{WHITE}" stroke="{BORDER}" stroke-width="1"/>'
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="8.5" '
            f'fill="{color}" text-anchor="middle" dominant-baseline="central"'
            f' font-weight="500">{xe(label)}</text>')

def tier_header(x, y, w, num, label, t):
    s  = rect(x, y, w, 38, t["s"], t["s"], rx=10, sw=0)
    s += rect(x, y+26, w, 12, t["s"], t["s"], rx=0, sw=0)
    s += txt(x + w//2 + 14, y+19, label, size=12, fill=WHITE, weight="bold")
    s += (f'<circle cx="{x+19}" cy="{y+19}" r="13" fill="{WHITE}" opacity="0.25"/>'
          f'<text x="{x+19}" y="{y+19}" font-family="{FONT}" font-size="12" '
          f'font-weight="bold" fill="{WHITE}" text-anchor="middle" '
          f'dominant-baseline="central">{xe(num)}</text>')
    return s

def tech_tag(x, y, label, t):
    cw = len(label) * 5.6 + 12
    return (f'<rect x="{x}" y="{y-8}" width="{cw}" height="16" rx="4" '
            f'fill="{t["cf"]}" stroke="{t["s"]}" stroke-width="0.8" opacity="0.7"/>'
            f'<text x="{x+cw/2}" y="{y}" font-family="{FONT}" font-size="7.5" '
            f'fill="{t["ct"]}" font-weight="500" text-anchor="middle" '
            f'dominant-baseline="central">{xe(label)}</text>')

def tech_tags_row(sx, y, labels, t, gap=4):
    out, cx = "", sx
    for l in labels:
        cw = len(l) * 5.6 + 12
        out += tech_tag(cx, y, l, t)
        cx += cw + gap
    return out

def step_row(x, y, w, num, plain_name, plain_desc, tech_hint, t):
    """A pipeline step row with: number badge, plain name, description, tech hint."""
    s  = rect(x, y-16, w, 34, t["cf"], t["s"], rx=8, sw=1)
    # Step number badge
    s += (f'<circle cx="{x+18}" cy="{y+1}" r="11" fill="{t["s"]}"/>'
          f'<text x="{x+18}" y="{y+1}" font-family="{FONT}" font-size="9" '
          f'font-weight="bold" fill="{WHITE}" text-anchor="middle" '
          f'dominant-baseline="central">{xe(num)}</text>')
    s += txt(x+36, y-5, plain_name, size=9.5, fill=t["ct"], weight="bold", anchor="start")
    s += txt(x+36, y+7, plain_desc, size=8,   fill=t["st"], anchor="start")
    # Tech hint on the right
    hint_x = x + w - 8
    s += txt(hint_x, y+1, tech_hint, size=7, fill=FAINT, anchor="end", italic=True)
    return s


# ── Layout ────────────────────────────────────────────────────────────────────
MX, MW = 55, 790
RX, RW = 875, 255
MC     = MX + MW//2   # main column centre

parts = []

# ── Defs ──────────────────────────────────────────────────────────────────────
parts.append("""<defs>
  <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M1 2 L8 5 L1 8" fill="none" stroke="context-stroke"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <filter id="sh" x="-4%" y="-4%" width="108%" height="115%">
    <feDropShadow dx="0" dy="2" stdDeviation="5"
                  flood-color="#0F172A" flood-opacity="0.07"/>
  </filter>
  <filter id="shSm" x="-5%" y="-5%" width="110%" height="120%">
    <feDropShadow dx="0" dy="1" stdDeviation="3"
                  flood-color="#0F172A" flood-opacity="0.06"/>
  </filter>
</defs>""")

# ── Background ────────────────────────────────────────────────────────────────
parts.append(f'<rect width="{W}" height="2000" fill="{BG}"/>')

# ── Title ─────────────────────────────────────────────────────────────────────
TC = W // 2
parts.append(txt(TC, 30, "FaultSense AI — How It Works",
                 size=22, fill=DARK, weight="bold"))
parts.append(txt(TC, 56,
                 "From a plain-English question to a diagnosed root cause and fix — in seconds",
                 size=11, fill=MID))
parts.append(txt(TC, 74,
                 "Telecom Network Fault Intelligence  ·  AI-Powered  ·  2026",
                 size=9, fill=FAINT))
parts.append(f'<line x1="{MX}" y1="88" x2="{RX+RW}" y2="88" '
             f'stroke="{BORDER}" stroke-width="1.5"/>')

# ── User bubble ───────────────────────────────────────────────────────────────
UY = 122
# Pill-shaped user card
parts.append(rect(MC-140, UY-30, 280, 58, WHITE, BORDER, rx=14, sw=1.5, filt="url(#shSm)"))
# Person icon
ux = MC - 108
parts.append(f'<circle cx="{ux}" cy="{UY-8}" r="6" fill="{FE["s"]}"/>')
parts.append(f'<path d="M {ux-9} {UY+10} Q {ux} {UY+2} {ux+9} {UY+10}" '
             f'fill="none" stroke="{FE["s"]}" stroke-width="2.2" stroke-linecap="round"/>')
parts.append(txt(MC+2, UY-8, "Network Operations Engineer",
                 size=12, fill=DARK, weight="700"))
parts.append(txt(MC+2, UY+10, "Types a question in plain English — no commands, no code",
                 size=9, fill=FAINT))

# Down arrow with label
parts.append(line(MC, UY+28, MC, UY+56, stroke=FE["s"], sw=2.2))
parts.append(flow_label(MC, UY+42, "Asks a question", FE["s"]))


# =============================================================================
# 1. WEB DASHBOARD  (React Frontend)
# =============================================================================
FY, FH = UY+58, 128
parts.append(rect(MX, FY, MW, FH, FE["f"], FE["s"], rx=12, filt="url(#sh)"))
parts.append(tier_header(MX, FY, MW, "1", "Web Dashboard", FE))

parts.append(txt(MX+16, FY+56, "Where engineers type questions and see the full diagnosis — charts, root cause, and step-by-step fix recommendations",
                 size=9.5, fill=MID, anchor="start"))

# Plain feature chips
features_fe = ["Ask a question", "View incident cards", "See AI reasoning steps",
                "Root cause panel", "Fix recommendations", "Analytics dashboard"]
cx, cy = MX+16, FY+82
for feat in features_fe:
    cw = len(feat)*6.2 + 16
    parts.append(rect(cx, cy-10, cw, 20, FE["cf"], FE["s"], rx=10, sw=0.8))
    parts.append(txt(cx+cw/2, cy, feat, size=8.5, fill=FE["ct"], weight="600"))
    cx += cw + 6
    if cx > MX+MW-100:
        cx, cy = MX+16, cy+26

parts.append(tech_tags_row(MX+16, FY+FH-14, ["React 18", "TypeScript", "Vite", "TailwindCSS"], FE))

# Arrow down
A1Y = FY + FH
parts.append(line(MC, A1Y, MC, A1Y+32, stroke=FE["s"], sw=2.5))
parts.append(flow_label(MC, A1Y+16, "Sends the question to the backend", FE["s"]))


# =============================================================================
# 2. PROCESSING ENGINE  (FastAPI Backend)
# =============================================================================
BY, BH = A1Y+34, 118
parts.append(rect(MX, BY, MW, BH, BE["f"], BE["s"], rx=12, filt="url(#sh)"))
parts.append(tier_header(MX, BY, MW, "2", "Processing Engine", BE))

parts.append(txt(MX+16, BY+54, "The brain of the system — receives questions, coordinates the AI agents, and sends the answer back to the dashboard",
                 size=9.5, fill=MID, anchor="start"))

# What it handles
handles = ["Receive questions", "Coordinate AI agents", "Load historical data",
           "Return diagnosis", "Track performance", "Quality evaluation"]
cx, cy = MX+16, BY+80
for h in handles:
    cw = len(h)*6.2 + 16
    parts.append(rect(cx, cy-10, cw, 20, BE["cf"], BE["s"], rx=10, sw=0.8))
    parts.append(txt(cx+cw/2, cy, h, size=8.5, fill=BE["ct"], weight="600"))
    cx += cw + 6

parts.append(tech_tags_row(MX+16, BY+BH-14, ["Python 3.11", "FastAPI", "Uvicorn", "Pydantic"], BE))


# ── Fork: Processing Engine → Knowledge Search + AI Analysis ─────────────────
fork_y = BY + BH + 20
RAG_X, RAG_W = MX, 378
LG_X,  LG_W  = MX+400, 390
TY = BY + BH + 46

parts.append(path(f"M {MC} {BY+BH} L {MC} {fork_y} "
                  f"L {RAG_X+RAG_W//2} {fork_y} L {RAG_X+RAG_W//2} {TY}",
                  stroke=RAG["s"], sw=2))
parts.append(path(f"M {MC} {BY+BH} L {MC} {fork_y} "
                  f"L {LG_X+LG_W//2} {fork_y} L {LG_X+LG_W//2} {TY}",
                  stroke=LG["s"], sw=2))
parts.append(flow_label(RAG_X+RAG_W//2 - 62, fork_y, "Search past incidents", RAG["s"]))
parts.append(flow_label(LG_X+LG_W//2  + 66, fork_y, "Run AI agent pipeline", LG["s"]))


# =============================================================================
# 3. KNOWLEDGE SEARCH  (RAG Pipeline)
# =============================================================================
TH_RAG = 192
parts.append(rect(RAG_X, TY, RAG_W, TH_RAG, RAG["f"], RAG["s"], rx=12, filt="url(#sh)"))
parts.append(tier_header(RAG_X, TY, RAG_W, "3", "Knowledge Search", RAG))

parts.append(txt(RAG_X+16, TY+52, "Searches 9,800+ real telecom incidents",
                 size=9.5, fill=MID, anchor="start", weight="600"))
parts.append(txt(RAG_X+16, TY+67, "to find the most relevant past cases",
                 size=9, fill=FAINT, anchor="start"))

rag_steps = [
    ("A", "Convert question to AI format",
     "Makes it possible to compare against all stored cases",
     "text-embedding-3-small"),
    ("B", "Search by meaning",
     "Finds incidents with similar context, even if words differ",
     "ChromaDB vector store"),
    ("C", "Search by keywords",
     "Finds exact keyword matches across incident descriptions",
     "BM25 full-text index"),
    ("D", "Combine & rank results",
     "Merges both searches to surface the best matches",
     "Hybrid RRF fusion"),
]
for i, (num, name, desc, hint) in enumerate(rag_steps):
    parts.append(step_row(RAG_X+10, TY+100+i*36, RAG_W-20, num, name, desc, hint, RAG))


# =============================================================================
# 4. AI ANALYSIS PIPELINE  (LangGraph Multi-Agent)
# =============================================================================
TH_LG = 224
parts.append(rect(LG_X, TY, LG_W, TH_LG, LG["f"], LG["s"], rx=12, filt="url(#sh)"))
parts.append(tier_header(LG_X, TY, LG_W, "4", "AI Analysis Pipeline", LG))

parts.append(txt(LG_X+16, TY+52, "4 AI agents work in sequence — each agent",
                 size=9.5, fill=MID, anchor="start", weight="600"))
parts.append(txt(LG_X+16, TY+67, "hands its findings to the next, like a relay team",
                 size=9, fill=FAINT, anchor="start"))

lg_steps = [
    ("1", "Safety Check",
     "Blocks harmful or irrelevant questions before they go further",
     "Guardrail agent"),
    ("2", "Find Similar Cases",
     "Retrieves the most relevant past incidents from the knowledge base",
     "Retrieval agent"),
    ("3", "Spot Patterns",
     "Groups incidents by location, network type, and timing to find clusters",
     "Correlation agent"),
    ("4", "Identify Root Cause",
     "Reasons through the evidence to pinpoint what actually went wrong",
     "Root-cause agent · GPT-4o"),
    ("5", "Suggest Fixes",
     "Produces clear, prioritised action steps the team can act on immediately",
     "Recommendations agent"),
]
for i, (num, name, desc, hint) in enumerate(lg_steps):
    parts.append(step_row(LG_X+10, TY+99+i*30, LG_W-20, num, name, desc, hint, LG))

# Dashed cross-arrow: Knowledge Search feeds AI Pipeline
mid_y = TY + max(TH_RAG, TH_LG)//2 - 10
parts.append(line(RAG_X+RAG_W, mid_y, LG_X, mid_y,
                  stroke=LG["s"], sw=1.5, dash="6 4"))
parts.append(flow_label((RAG_X+RAG_W+LG_X)//2, mid_y-14,
                         "Relevant cases passed to agents", LG["s"]))


# =============================================================================
# 5. DATA STORE  (Storage Layer)
# =============================================================================
# Use the taller of the two panels to set SY
TH_MAX = max(TH_RAG, TH_LG)
SY = TY + TH_MAX + 30
SH = 86
parts.append(rect(MX, SY, MW, SH, ST["f"], ST["s"], rx=12, filt="url(#sh)"))
parts.append(tier_header(MX, SY, MW, "5", "Data Store", ST))

stores = [
    ("📄", "Historical Incidents",     "9,827 real telecom fault records",         BE),
    ("🧠", "AI Memory (Vector DB)",    "Stores questions as searchable AI patterns", OAI),
    ("🔍", "Keyword Search Index",     "Fast full-text lookup across all incidents",  RAG),
]
SI_W = 238
si_gap = (MW - 3 * SI_W) / 4
for i, (icon, name, desc, t) in enumerate(stores):
    sx = MX + si_gap + i * (SI_W + si_gap)
    parts.append(rect(sx, SY+42, SI_W, 38, t["cf"], t["s"], rx=8, sw=1))
    parts.append(txt(sx+14, SY+61, icon, size=16, fill=t["ct"], anchor="start"))
    parts.append(txt(sx+38, SY+54, name, size=9.5, fill=t["ct"], weight="bold", anchor="start"))
    parts.append(txt(sx+38, SY+68, desc, size=7.5, fill=t["st"], anchor="start"))

# Arrow: Knowledge Search → Data Store
RCX = RAG_X + RAG_W//2
parts.append(line(RCX, TY+TH_RAG, RCX, SY, stroke=RAG["s"], sw=1.8))
parts.append(flow_label(RCX+50, TY+TH_RAG+14, "Read & write data", RAG["s"]))


# =============================================================================
# RIGHT COLUMN — External Services
# =============================================================================
def ext_box(x, y, w, num, icon, title, subtitle, bullets, tech_bullets, t):
    h = 38 + 22 + len(bullets)*22 + 18 + (len(tech_bullets)*16 + 8 if tech_bullets else 0) + 12
    s  = rect(x, y, w, h, t["f"], t["s"], rx=12, sw=1.5, filt="url(#shSm)")
    s += tier_header(x, y, w, num, f"{icon}  {title}", t)
    s += txt(x+16, y+50, subtitle, size=8.5, fill=MID, anchor="start", weight="600")
    for j, b in enumerate(bullets):
        row_y = y + 66 + j*22
        s += (f'<circle cx="{x+20}" cy="{row_y}" r="3.5" fill="{t["s"]}"/>')
        s += txt(x+34, row_y, b, size=8.5, fill=t["ct"], anchor="start")
    if tech_bullets:
        sep_y = y + 66 + len(bullets)*22 + 4
        s += f'<line x1="{x+12}" y1="{sep_y}" x2="{x+w-12}" y2="{sep_y}" stroke="{BORDER}" stroke-width="1"/>'
        s += txt(x+16, sep_y+10, "Under the hood:", size=7.5, fill=FAINT, anchor="start", italic=True)
        for j, b in enumerate(tech_bullets):
            s += txt(x+16, sep_y+22+j*16, b, size=7.5, fill=FAINT, anchor="start")
    return s, h

OAI_Y = BY
oai_box, OAI_H = ext_box(
    RX, OAI_Y, RW, "6", "🤖", "AI Language Model",
    "Powers all reasoning & text generation",
    ["Understands natural language questions",
     "Reasons step-by-step like an expert",
     "Generates clear, structured answers"],
    ["GPT-4o-mini / GPT-4o", "text-embedding-3-small", "OpenAI API"],
    OAI)
parts.append(oai_box)

LS_Y = OAI_Y + OAI_H + 16
ls_box, LS_H = ext_box(
    RX, LS_Y, RW, "7", "📈", "Activity Monitor",
    "Records every step the AI takes",
    ["Tracks how long each agent runs",
     "Helps the team tune performance",
     "Flags slow or failing steps"],
    ["LangSmith · LANGCHAIN_TRACING_V2"],
    LS)
parts.append(ls_box)

DE_Y = LS_Y + LS_H + 16
de_box, DE_H = ext_box(
    RX, DE_Y, RW, "8", "✅", "Quality Checker",
    "Scores the AI's answers automatically",
    ["Is the answer faithful to the evidence?",
     "Is it relevant to what was asked?",
     "Is the supporting context accurate?"],
    ["DeepEval · LLM-as-judge scoring"],
    DE)
parts.append(de_box)


# ── Right-column connection arrows ────────────────────────────────────────────
BE_RX  = MX + MW
OAI_LX = RX
OAI_CY = OAI_Y + OAI_H//2
LS_CY  = LS_Y  + LS_H//2
DE_CY  = DE_Y  + DE_H//2

# Processing Engine → AI Language Model
BY_C = BY + BH//2
parts.append(line(BE_RX, BY_C, OAI_LX, OAI_CY, stroke=OAI["s"], sw=1.8))
parts.append(flow_label((BE_RX+OAI_LX)//2, BY_C-14, "AI calls", OAI["s"]))

# Knowledge Search → AI Language Model (dashed, embedding)
R_RX = RAG_X + RAG_W
R_MY = TY + TH_RAG//2 - 20
parts.append(path(f"M {R_RX} {R_MY} L {BE_RX+22} {R_MY} "
                  f"L {BE_RX+22} {OAI_CY+22} L {OAI_LX} {OAI_CY+22}",
                  stroke=OAI["s"], sw=1.5, dash="5 4"))
parts.append(flow_label(BE_RX+22, R_MY-14, "Convert to AI format", OAI["s"]))

# AI Analysis Pipeline → AI Language Model
L_RX = LG_X + LG_W
L_MY = TY + TH_LG//2 + 18
parts.append(path(f"M {L_RX} {L_MY} L {OAI_LX} {L_MY} "
                  f"L {OAI_LX} {OAI_CY-12}",
                  stroke=OAI["s"], sw=1.8))
parts.append(flow_label((L_RX+OAI_LX)//2, L_MY-14, "Generate diagnosis", OAI["s"]))

# Processing Engine → Activity Monitor (dashed)
parts.append(path(f"M {BE_RX} {BY+BH*0.68} L {OAI_LX-12} {BY+BH*0.68} "
                  f"L {OAI_LX-12} {LS_CY} L {OAI_LX} {LS_CY}",
                  stroke=LS["s"], sw=1.5, dash="5 4"))
parts.append(flow_label(BE_RX+24, BY+BH*0.68-14, "Log activity", LS["s"]))

# Processing Engine → Quality Checker
parts.append(path(f"M {BE_RX} {BY+BH*0.88} L {OAI_LX-24} {BY+BH*0.88} "
                  f"L {OAI_LX-24} {DE_CY} L {OAI_LX} {DE_CY}",
                  stroke=DE["s"], sw=1.8))
parts.append(flow_label(BE_RX+24, BY+BH*0.88-14, "Score answer", DE["s"]))


# =============================================================================
# LEGEND
# =============================================================================
LEG_Y = SY + SH + 24
LEG_H = 54
LTOT  = RX + RW - MX
parts.append(rect(MX, LEG_Y, LTOT, LEG_H, WHITE, BORDER, rx=8, sw=1))
parts.append(txt(MX+16, LEG_Y+16, "Components:", size=9,
                 fill=MID, weight="bold", anchor="start"))

leg_data = [
    ("Web Dashboard",      FE,  "⚛"),
    ("Processing Engine",  BE,  "⚙"),
    ("Knowledge Search",   RAG, "🔍"),
    ("AI Agent Pipeline",  LG,  "🤖"),
    ("Data Store",         ST,  "🗂"),
    ("AI Language Model",  OAI, "💬"),
    ("Activity Monitor",   LS,  "📈"),
    ("Quality Checker",    DE,  "✅"),
]
chip_widths = [len(label)*6.4 + 32 for _, _, label in [(t, c, n) for n, c, t in leg_data]]
LABEL_W = 100
avail_w = LTOT - LABEL_W
total_cw = sum(chip_widths)
gap = (avail_w - total_cw) / (len(leg_data) + 1)
lx = MX + LABEL_W + gap
for (name, t, icon), cw in zip(leg_data, chip_widths):
    parts.append(rect(lx, LEG_Y+26, cw, 20, t["cf"], t["s"], rx=5, sw=0.8))
    parts.append(txt(lx+8,  LEG_Y+36, icon, size=10, fill=t["ct"], anchor="start"))
    parts.append(txt(lx+24, LEG_Y+36, name, size=8,  fill=t["ct"], weight="600", anchor="start"))
    lx += cw + gap


# =============================================================================
# FOOTER
# =============================================================================
FT_Y = LEG_Y + LEG_H + 12
parts.append(f'<line x1="{MX}" y1="{FT_Y}" x2="{RX+RW}" y2="{FT_Y}" '
             f'stroke="{BORDER}" stroke-width="1"/>')
parts.append(txt(TC, FT_Y+14,
    "FaultSense AI  ·  AI-Powered Telecom Fault Intelligence  ·  "
    "RAG + Multi-Agent AI + Automated Quality Scoring  ·  2026",
    size=8.5, fill=FAINT))


# ── Assemble SVG ──────────────────────────────────────────────────────────────
TOTAL_H = FT_Y + 30
svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{W}" height="{TOTAL_H}" viewBox="0 0 {W} {TOTAL_H}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     style="font-family:{FONT}; background:{BG}">
<title>FaultSense AI — How It Works</title>
<desc>Presentation-friendly architecture diagram showing the end-to-end flow
from a plain-English question to a diagnosed root cause and fix recommendations.
Designed for mixed technical and non-technical audiences.</desc>
{''.join(parts)}
</svg>"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"SVG written: {OUT}  ({TOTAL_H}px tall)")
