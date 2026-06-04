"""
Generates two high-level flow SVGs:
  QUICKSEARCH_FLOW.svg  — 5 steps
  DEEPANALYSIS_FLOW.svg — 6 steps
Run: python generate_flow_diagrams.py
"""
import os, html

BASE = os.path.dirname(__file__)
FONT = "'Segoe UI', -apple-system, 'Inter', sans-serif"


def xe(s):
    return html.escape(str(s))


# ─────────────────────────────────────────────────────────────────────────────
# SHARED SVG BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_flow_svg(title, subtitle, header_color, steps, w=1200, h=500):
    """
    steps: list of dicts with keys:
      emoji, title, sub, lines (list of 2 strings),
      accent, light, ring, arrow_label (str or "")
    """
    TITLE_H  = 88
    CW       = 168 if len(steps) == 5 else 148
    CH       = 265
    ARROW_W  = 52  if len(steps) == 5 else 44
    GAP_TOP  = TITLE_H + 28

    N        = len(steps)
    TOTAL_W  = N * CW + (N - 1) * ARROW_W
    CARD_X0  = (w - TOTAL_W) // 2
    CARD_CY  = GAP_TOP + CH // 2

    p = []

    # ── SVG open ──────────────────────────────────────────────────────────
    p.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     style="font-family:{FONT}; background:#F8FAFC">
<title>{xe(title)}</title>""")

    # ── Defs — single block with all markers ─────────────────────────────
    defs_parts = ["<defs>"]
    for i in range(len(steps) - 1):
        mid = f"arr{i}"
        c   = steps[i + 1]["accent"]
        defs_parts.append(
            f'  <marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M1 2 L8 5 L1 8" fill="none" stroke="{c}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</marker>'
        )
    defs_parts.append(
        '  <filter id="sh">'
        '<feDropShadow dx="0" dy="3" stdDeviation="6" '
        'flood-color="#0F172A" flood-opacity="0.10"/>'
        '</filter>'
    )
    defs_parts.append("</defs>")
    p.append("\n".join(defs_parts))

    # ── Background ────────────────────────────────────────────────────────
    p.append(f'<rect width="{w}" height="{h}" fill="#F8FAFC"/>')
    # Dot grid
    p.append(f"""<defs>
  <pattern id="dg" x="0" y="0" width="30" height="30" patternUnits="userSpaceOnUse">
    <circle cx="15" cy="15" r="1.1" fill="#CBD5E1" opacity="0.45"/>
  </pattern>
</defs>
<rect width="{w}" height="{h}" fill="url(#dg)"/>""")

    # ── Title banner ──────────────────────────────────────────────────────
    p.append(f"""<rect x="0" y="0" width="{w}" height="{TITLE_H}" fill="{header_color}"/>
<rect x="0" y="{TITLE_H - 5}" width="{w}" height="5" fill="#F26B43"/>
<text x="{w // 2}" y="34" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="21" font-weight="800" fill="#F8FAFC">
  {xe(title)}
</text>
<text x="{w // 2}" y="63" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="11" fill="#94A3B8">
  {xe(subtitle)}
</text>""")

    # ── Dashed spine ──────────────────────────────────────────────────────
    p.append(f"""<line x1="{CARD_X0}" y1="{CARD_CY}"
      x2="{CARD_X0 + TOTAL_W}" y2="{CARD_CY}"
      stroke="#E2E8F0" stroke-width="1" stroke-dasharray="5 7"/>""")

    # ── Cards + arrows ────────────────────────────────────────────────────
    for i, step in enumerate(steps):
        cx = CARD_X0 + i * (CW + ARROW_W)
        cy = GAP_TOP
        acc  = step["accent"]
        lite = step["light"]
        ring = step["ring"]
        icx  = cx + CW // 2
        icy  = cy + 76

        # Card
        p.append(f"""
<!-- Card {i+1}: {step['title']} -->
<rect x="{cx}" y="{cy}" width="{CW}" height="{CH}" rx="15"
      fill="{lite}" stroke="{acc}" stroke-width="1.8" filter="url(#sh)"/>
<rect x="{cx}" y="{cy}" width="{CW}" height="8" rx="15" fill="{acc}"/>
<rect x="{cx}" y="{cy+4}" width="{CW}" height="4" fill="{acc}"/>""")

        # Step badge
        p.append(f"""<circle cx="{cx + 22}" cy="{cy + 32}" r="15" fill="{acc}"/>
<text x="{cx + 22}" y="{cy + 32}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="11" font-weight="800" fill="white">{xe(step['num'])}</text>""")

        # Outer glow ring
        p.append(f"""<circle cx="{icx}" cy="{icy}" r="38" fill="{ring}" opacity="0.55"/>""")
        # Icon circle
        p.append(f"""<circle cx="{icx}" cy="{icy}" r="30"
      fill="{lite}" stroke="{acc}" stroke-width="2.2"/>
<text x="{icx}" y="{icy}" text-anchor="middle" dominant-baseline="central"
      font-size="26">{xe(step['emoji'])}</text>""")

        # Title
        ty = icy + 50
        p.append(f"""<text x="{icx}" y="{ty}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="13.5" font-weight="700" fill="#0F172A">{xe(step['title'])}</text>""")

        # Sub
        p.append(f"""<text x="{icx}" y="{ty + 21}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="10" font-weight="600" fill="{acc}">{xe(step['sub'])}</text>""")

        # Divider
        p.append(f"""<line x1="{cx + 16}" y1="{ty + 35}" x2="{cx + CW - 16}" y2="{ty + 35}"
      stroke="#E2E8F0" stroke-width="1.2"/>""")

        # Detail lines
        for j, line in enumerate(step["lines"]):
            ly = ty + 51 + j * 21
            p.append(f"""<text x="{icx}" y="{ly}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="9" fill="#475569">{xe(line)}</text>""")

        # Arrow to next
        if i < N - 1:
            ax1 = cx + CW + 4
            ax2 = cx + CW + ARROW_W - 4
            ay  = CARD_CY
            mid = f"arr{i}"
            nc  = steps[i + 1]["accent"]
            lbl = step.get("arrow_label", "")

            p.append(f"""<line x1="{ax1}" y1="{ay}" x2="{ax2}" y2="{ay}"
      stroke="{nc}" stroke-width="2.5" stroke-linecap="round"
      marker-end="url(#{mid})"/>""")

            if lbl:
                mx = (ax1 + ax2) // 2
                lw = len(lbl) * 7 + 16
                p.append(f"""<rect x="{mx - lw//2}" y="{ay - 13}" width="{lw}" height="21"
      rx="10" fill="white" stroke="{nc}" stroke-width="1"/>
<text x="{mx}" y="{ay - 2}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="8.5" font-weight="600" fill="{nc}">{xe(lbl)}</text>""")

    # ── Bottom tech bar ───────────────────────────────────────────────────
    BY = GAP_TOP + CH + 20
    p.append(f"""<rect x="{CARD_X0}" y="{BY}" width="{TOTAL_W}" height="36" rx="8"
      fill="#1E293B"/>""")
    cw_each = TOTAL_W / N
    for i, step in enumerate(steps):
        lx = CARD_X0 + i * cw_each + cw_each / 2
        label = step.get("tech", "")
        p.append(f"""<text x="{lx:.1f}" y="{BY + 18}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="8.5" fill="#94A3B8" font-style="italic">{xe(label)}</text>""")

    # Footer
    p.append(f"""<text x="{w // 2}" y="{h - 11}" text-anchor="middle"
      font-family="{FONT}" font-size="8.5" fill="#CBD5E1">
  FaultSense AI  ·  Telecom Network Fault Intelligence  ·  2026
</text>""")

    p.append("</svg>")
    return "\n".join(p)


# ═════════════════════════════════════════════════════════════════════════════
# QUICK SEARCH FLOW
# ═════════════════════════════════════════════════════════════════════════════
qs_steps = [
    {
        "num":   "1",
        "emoji": "🔎",
        "title": "User Query",
        "sub":   "Plain English Input",
        "lines": ["Type your fault description", "No technical knowledge needed"],
        "accent": "#475569",
        "light":  "#F8FAFC",
        "ring":   "#E2E8F0",
        "tech":   "React QueryInput",
        "arrow_label": "validate",
    },
    {
        "num":   "2",
        "emoji": "🛡",
        "title": "Guardrail Check",
        "sub":   "Input Validation",
        "lines": ["Is the query safe?", "Is it telecom-related?"],
        "accent": "#EA580C",
        "light":  "#FFF7ED",
        "ring":   "#FED7AA",
        "tech":   "guardrails.py",
        "arrow_label": "search",
    },
    {
        "num":   "3",
        "emoji": "🔍",
        "title": "Hybrid Search",
        "sub":   "Find Similar Incidents",
        "lines": ["Semantic + keyword search", "Best matches ranked by score"],
        "accent": "#1D4ED8",
        "light":  "#EFF6FF",
        "ring":   "#BFDBFE",
        "tech":   "ChromaDB + BM25 + RRF",
        "arrow_label": "suggest",
    },
    {
        "num":   "4",
        "emoji": "💡",
        "title": "Quick Root Cause",
        "sub":   "AI Suggestion",
        "lines": ["AI reads similar incidents", "Suggests likely root cause"],
        "accent": "#D97706",
        "light":  "#FFFBEB",
        "ring":   "#FDE68A",
        "tech":   "GPT-4o · 2-3 sentences",
        "arrow_label": "display",
    },
    {
        "num":   "5",
        "emoji": "📋",
        "title": "Results Shown",
        "sub":   "Incident Cards + Scores",
        "lines": ["Ranked incident cards", "Severity badges · RRF scores"],
        "accent": "#16A34A",
        "light":  "#F0FDF4",
        "ring":   "#BBF7D0",
        "tech":   "React IncidentCard",
        "arrow_label": "",
    },
]

qs_svg = build_flow_svg(
    title    = "🔎  Quick Search Flow  —  FaultSense AI",
    subtitle = "Fast hybrid retrieval with an inline AI root cause suggestion — results in seconds",
    header_color = "#1D4ED8",
    steps    = qs_steps,
)

qs_out = os.path.join(BASE, "QUICKSEARCH_FLOW.svg")
with open(qs_out, "w", encoding="utf-8") as f:
    f.write(qs_svg)
print(f"Quick Search SVG: {qs_out}  ({os.path.getsize(qs_out):,} bytes)")


# ═════════════════════════════════════════════════════════════════════════════
# DEEP ANALYSIS FLOW
# ═════════════════════════════════════════════════════════════════════════════
da_steps = [
    {
        "num":   "1",
        "emoji": "🔎",
        "title": "User Query",
        "sub":   "Plain English Input",
        "lines": ["Type your fault description", "Deep investigation requested"],
        "accent": "#475569",
        "light":  "#F8FAFC",
        "ring":   "#E2E8F0",
        "tech":   "React QueryInput",
        "arrow_label": "validate",
    },
    {
        "num":   "2",
        "emoji": "🛡",
        "title": "Guardrail Check",
        "sub":   "Safety & Relevance",
        "lines": ["3 checks: safety, injection,", "telecom relevance"],
        "accent": "#EA580C",
        "light":  "#FFF7ED",
        "ring":   "#FED7AA",
        "tech":   "guardrails.py",
        "arrow_label": "retrieve",
    },
    {
        "num":   "3",
        "emoji": "📚",
        "title": "Retrieve Incidents",
        "sub":   "Find Related Alarms",
        "lines": ["Searches incident history", "Ranks top matches"],
        "accent": "#1D4ED8",
        "light":  "#EFF6FF",
        "ring":   "#BFDBFE",
        "tech":   "Hybrid RAG · RRF fusion",
        "arrow_label": "correlate",
    },
    {
        "num":   "4",
        "emoji": "🔗",
        "title": "Correlate Alarms",
        "sub":   "Find Patterns",
        "lines": ["Groups alarms by region", "Identifies affected vendors"],
        "accent": "#D97706",
        "light":  "#FFFBEB",
        "ring":   "#FDE68A",
        "tech":   "utils/correlation.py",
        "arrow_label": "analyse",
    },
    {
        "num":   "5",
        "emoji": "🎯",
        "title": "AI Analysis",
        "sub":   "Root Cause + Impact",
        "lines": ["Explains why it happened", "Assesses service impact"],
        "accent": "#7C3AED",
        "light":  "#F5F3FF",
        "ring":   "#DDD6FE",
        "tech":   "GPT-4o · LangGraph nodes 3 & 4",
        "arrow_label": "generate",
    },
    {
        "num":   "6",
        "emoji": "✅",
        "title": "Recommendations",
        "sub":   "Actions + Evaluation",
        "lines": ["Step-by-step fix guide", "Auto quality score computed"],
        "accent": "#16A34A",
        "light":  "#F0FDF4",
        "ring":   "#BBF7D0",
        "tech":   "Node 5 · DeepEval metrics",
        "arrow_label": "",
    },
]

da_svg = build_flow_svg(
    title    = "🧠  Deep Analysis Flow  —  FaultSense AI",
    subtitle = "Full 5-node AI agent pipeline from alarm to root cause, service impact, and step-by-step fix",
    header_color = "#4C1D95",
    steps    = da_steps,
    h        = 500,
)

da_out = os.path.join(BASE, "DEEPANALYSIS_FLOW.svg")
with open(da_out, "w", encoding="utf-8") as f:
    f.write(da_svg)
print(f"Deep Analysis SVG: {da_out}  ({os.path.getsize(da_out):,} bytes)")
