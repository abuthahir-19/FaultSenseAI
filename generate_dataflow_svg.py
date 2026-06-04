"""
Generates DATAFLOW_DIAGRAM.svg — attractive 5-step data pipeline diagram.
Run: python generate_dataflow_svg.py
"""
import os, html

OUT = os.path.join(os.path.dirname(__file__), "DATAFLOW_DIAGRAM.svg")

W, H = 1200, 500

# ── Step definitions ──────────────────────────────────────────────────────────
steps = [
    {
        "num":    "01",
        "emoji":  "📄",
        "title":  "CSV File",
        "sub":    "telecom_incidents.csv",
        "lines":  ["9,827 incident records", "10 fields per row"],
        "accent": "#16A34A",   # green
        "light":  "#F0FDF4",
        "ring":   "#BBF7D0",
        "arrow_label": "trigger",
    },
    {
        "num":    "02",
        "emoji":  "⚡",
        "title":  "Ingestion Pipeline",
        "sub":    "Backend Worker",
        "lines":  ["POST /api/ingest", "Background task"],
        "accent": "#1D4ED8",   # blue
        "light":  "#EFF6FF",
        "ring":   "#BFDBFE",
        "arrow_label": "vectorise",
    },
    {
        "num":    "03",
        "emoji":  "🧠",
        "title":  "Generate Embeddings",
        "sub":    "text-embedding-3-small",
        "lines":  ["OpenAI API", "3 workers · batch 512"],
        "accent": "#D97706",   # amber
        "light":  "#FFFBEB",
        "ring":   "#FDE68A",
        "arrow_label": "store",
    },
    {
        "num":    "04",
        "emoji":  "🗄",
        "title":  "Store in ChromaDB",
        "sub":    "Vector Database",
        "lines":  ["Persistent local store", "1536-dim vectors"],
        "accent": "#7C3AED",   # violet
        "light":  "#F5F3FF",
        "ring":   "#DDD6FE",
        "arrow_label": "index",
    },
    {
        "num":    "05",
        "emoji":  "🔍",
        "title":  "Build BM25 Index",
        "sub":    "Keyword Search Index",
        "lines":  ["rank_bm25 library", "In-memory index"],
        "accent": "#0F766E",   # teal
        "light":  "#F0FDFA",
        "ring":   "#99F6E4",
        "arrow_label": "",
    },
]

# ── Layout ────────────────────────────────────────────────────────────────────
TITLE_H  = 90       # title banner height
CW       = 178      # card width
CH       = 270      # card height
ARROW_W  = 54       # arrow connector width
GAP_TOP  = TITLE_H + 30   # y where cards start = 120

N = len(steps)
TOTAL_W  = N * CW + (N-1) * ARROW_W          # 5*178 + 4*54 = 1106
CARD_X0  = (W - TOTAL_W) // 2                 # 47

CARD_CY  = GAP_TOP + CH // 2                  # vertical centre of cards
FONT     = "'Segoe UI', -apple-system, 'Inter', sans-serif"


def xe(s): return html.escape(str(s))


parts = []

# ── SVG open ──────────────────────────────────────────────────────────────────
parts.append(f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     xmlns="http://www.w3.org/2000/svg" role="img"
     style="font-family:{FONT}; background:#F8FAFC">
<title>FaultSense AI — Data Flow Pipeline</title>
<desc>5-step pipeline: CSV File to Ingestion to Embeddings to ChromaDB to BM25 Index</desc>""")

# ── Defs ──────────────────────────────────────────────────────────────────────
parts.append("""<defs>
  <!-- arrowhead marker for each step colour -->
  <marker id="arr-g" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1 2 L8 5 L1 8" fill="none" stroke="#16A34A"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="arr-b" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1 2 L8 5 L1 8" fill="none" stroke="#1D4ED8"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="arr-a" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1 2 L8 5 L1 8" fill="none" stroke="#D97706"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <marker id="arr-v" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M1 2 L8 5 L1 8" fill="none" stroke="#7C3AED"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  </marker>
  <filter id="shadow">
    <feDropShadow dx="0" dy="3" stdDeviation="5"
                  flood-color="#0F172A" flood-opacity="0.10"/>
  </filter>
  <filter id="glow">
    <feDropShadow dx="0" dy="0" stdDeviation="6"
                  flood-color="#0F172A" flood-opacity="0.08"/>
  </filter>
</defs>""")

# ── Background ────────────────────────────────────────────────────────────────
parts.append(f'<rect width="{W}" height="{H}" fill="#F8FAFC"/>')

# Subtle dot-grid background
parts.append(f"""<pattern id="dots" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
  <circle cx="14" cy="14" r="1.2" fill="#CBD5E1" opacity="0.5"/>
</pattern>
<rect width="{W}" height="{H}" fill="url(#dots)"/>""")

# ── Title banner ──────────────────────────────────────────────────────────────
parts.append(f"""
<!-- Title banner -->
<rect x="0" y="0" width="{W}" height="{TITLE_H}" rx="0"
      fill="#0F172A"/>
<rect x="0" y="{TITLE_H-4}" width="{W}" height="4" fill="#F26B43"/>

<text x="{W//2}" y="36" text-anchor="middle"
      font-family="{FONT}" font-size="22" font-weight="800" fill="#F8FAFC"
      dominant-baseline="central">
  📊  Data Flow Pipeline  —  FaultSense AI
</text>
<text x="{W//2}" y="66" text-anchor="middle"
      font-family="{FONT}" font-size="12" fill="#94A3B8"
      dominant-baseline="central">
  How raw incident data flows from a CSV file to a fully searchable AI knowledge base
</text>""")

# ── Step cards + arrows ───────────────────────────────────────────────────────
arrow_markers = ["arr-g", "arr-b", "arr-a", "arr-v"]

for i, step in enumerate(steps):
    cx = CARD_X0 + i * (CW + ARROW_W)
    cy = GAP_TOP
    acc  = step["accent"]
    lite = step["light"]
    ring = step["ring"]

    # ── Card shadow + base ────────────────────────────────────────────────
    parts.append(f"""
<!-- Card {i+1}: {step['title']} -->
<rect x="{cx}" y="{cy}" width="{CW}" height="{CH}" rx="16"
      fill="{lite}" filter="url(#shadow)"
      stroke="{acc}" stroke-width="1.8"/>""")

    # Accent top strip
    parts.append(f"""<rect x="{cx}" y="{cy}" width="{CW}" height="8" rx="16"
      fill="{acc}"/>
<rect x="{cx}" y="{cy+4}" width="{CW}" height="4" fill="{acc}"/>""")

    # Step number badge (top-left)
    parts.append(f"""<circle cx="{cx+22}" cy="{cy+32}" r="16" fill="{acc}"/>
<text x="{cx+22}" y="{cy+32}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="11" font-weight="800" fill="white">{xe(step['num'])}</text>""")

    # Emoji icon circle (centered horizontally)
    icon_cx = cx + CW // 2
    icon_cy = cy + 76
    parts.append(f"""<circle cx="{icon_cx}" cy="{icon_cy}" r="36"
      fill="{ring}" opacity="0.7"/>
<circle cx="{icon_cx}" cy="{icon_cy}" r="30"
      fill="{lite}" stroke="{acc}" stroke-width="2"/>
<text x="{icon_cx}" y="{icon_cy}" text-anchor="middle" dominant-baseline="central"
      font-size="28">{xe(step['emoji'])}</text>""")

    # Title
    ty = icon_cy + 50
    parts.append(f"""<text x="{cx + CW//2}" y="{ty}" text-anchor="middle"
      font-family="{FONT}" font-size="14" font-weight="700" fill="#0F172A"
      dominant-baseline="central">{xe(step['title'])}</text>""")

    # Sub-title
    parts.append(f"""<text x="{cx + CW//2}" y="{ty+22}" text-anchor="middle"
      font-family="{FONT}" font-size="10" font-weight="600" fill="{acc}"
      dominant-baseline="central">{xe(step['sub'])}</text>""")

    # Divider
    parts.append(f"""<line x1="{cx+18}" y1="{ty+36}" x2="{cx+CW-18}" y2="{ty+36}"
      stroke="#E2E8F0" stroke-width="1.2"/>""")

    # Detail lines
    for j, line in enumerate(step["lines"]):
        ly = ty + 52 + j * 20
        parts.append(f"""<text x="{cx + CW//2}" y="{ly}" text-anchor="middle"
      font-family="{FONT}" font-size="9.5" fill="#475569"
      dominant-baseline="central">{xe(line)}</text>""")

    # ── Arrow to next step ────────────────────────────────────────────────
    if i < len(steps) - 1:
        ax1 = cx + CW + 4
        ax2 = cx + CW + ARROW_W - 4
        ay  = GAP_TOP + CH // 2
        marker = arrow_markers[i]
        next_acc = steps[i+1]["accent"]
        lbl = step["arrow_label"]

        # Arrow line
        parts.append(f"""
<!-- Arrow {i+1}→{i+2} -->
<line x1="{ax1}" y1="{ay}" x2="{ax2}" y2="{ay}"
      stroke="{next_acc}" stroke-width="2.5"
      marker-end="url(#{marker})" stroke-linecap="round"/>""")

        # Arrow label pill
        if lbl:
            mx = (ax1 + ax2) // 2
            lw = len(lbl) * 7 + 14
            parts.append(f"""<rect x="{mx - lw//2}" y="{ay-12}" width="{lw}" height="20"
      rx="10" fill="white" stroke="{next_acc}" stroke-width="1"/>
<text x="{mx}" y="{ay-2}" text-anchor="middle" dominant-baseline="central"
      font-family="{FONT}" font-size="8.5" font-weight="600" fill="{next_acc}">{xe(lbl)}</text>""")

# ── Bottom bar ────────────────────────────────────────────────────────────────
BY = GAP_TOP + CH + 22
parts.append(f"""
<!-- Bottom summary bar -->
<rect x="{CARD_X0}" y="{BY}" width="{TOTAL_W}" height="38" rx="8"
      fill="#1E293B"/>""")

tech_labels = [
    "pandas · CSV reader",
    "FastAPI BackgroundTask",
    "OpenAI text-embedding-3-small",
    "ChromaDB persistent",
    "rank_bm25 library",
]
lw_each = TOTAL_W / len(tech_labels)
for i, label in enumerate(tech_labels):
    lx = CARD_X0 + i * lw_each + lw_each / 2
    parts.append(f"""<text x="{lx:.1f}" y="{BY+19}" text-anchor="middle"
      font-family="{FONT}" font-size="9" fill="#94A3B8" dominant-baseline="central"
      font-style="italic">{xe(label)}</text>""")

# Tech badges along the top connector line
connector_y = GAP_TOP + CH // 2
parts.append(f"""
<!-- Full-width flow spine -->
<line x1="{CARD_X0}" y1="{connector_y}" x2="{CARD_X0 + TOTAL_W}" y2="{connector_y}"
      stroke="#E2E8F0" stroke-width="1" stroke-dasharray="4 6"/>""")

# Footer
parts.append(f"""
<text x="{W//2}" y="{H-12}" text-anchor="middle"
      font-family="{FONT}" font-size="9" fill="#CBD5E1">
  FaultSense AI  ·  Telecom Network Fault Intelligence Platform  ·  2026
</text>""")

# ── Close SVG ─────────────────────────────────────────────────────────────────
parts.append("</svg>")

svg = "\n".join(parts)

with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)

print(f"SVG created: {OUT}")
print(f"Size: {os.path.getsize(OUT):,} bytes")
