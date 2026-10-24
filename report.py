"""Branded PDF report -> bytes."""
import io, re, datetime as dt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart

NAVY, GREEN, RED = colors.HexColor("#0B1F3A"), colors.HexColor("#16A34A"), colors.HexColor("#DC2626")
ss = getSampleStyleSheet()
H = ParagraphStyle("H", parent=ss["Heading2"], textColor=NAVY, spaceBefore=10)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)

def _tbl(data, widths=None):
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
          ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
          ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#CBD5E1")), ("ALIGN", (1, 0), (-1, -1), "RIGHT")]
    for r, row in enumerate(data[1:], 1):
        for c, v in enumerate(row):
            if isinstance(v, str) and v.startswith(("+", "-")) and v.endswith("%"):
                st.append(("TEXTCOLOR", (c, r), (c, r), GREEN if v[0] == "+" else RED))
            if v in ("BUY", "AVOID"): st.append(("TEXTCOLOR", (c, r), (c, r), GREEN if v == "BUY" else RED))
    t.setStyle(TableStyle(st)); return t

def _md(text):
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("|"): continue   # tables are rendered natively below
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line.replace("&", "&amp;"))
        if line.startswith("#"): out.append(Paragraph(line.lstrip("# "), H))
        else: out.append(Paragraph(("• " + line[2:]) if line[:2] in ("- ", "* ") else line, B))
    return out

def build_pdf(result: dict, query: str = "Market overview") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm,
                            title="MarketPulse Report")
    s = [Paragraph("MarketPulse — Market Intelligence Report", ParagraphStyle("T", parent=ss["Title"], textColor=NAVY)),
         Paragraph(f"Query: <i>{query}</i> &nbsp;|&nbsp; Window: {result['intent']['period']} &nbsp;|&nbsp; {dt.datetime.now():%d %b %Y, %H:%M}", B),
         Spacer(1, 6), Paragraph("Indices", H)]
    f = lambda v, p=True: "n/a" if v != v else (f"{v:+.2f}%" if p else f"{v:,.2f}")
    s.append(_tbl([["Index", "Level", "Day", "Period"]] + [[r["Index"], f(r["Level"], False), f(r["Day %"]), f(r["Period %"])] for r in result["indices"].to_dict("records")]))
    sec = result["sectors"]
    d = Drawing(480, 18 * len(sec) + 30)
    bc = HorizontalBarChart(); bc.x, bc.y, bc.width, bc.height = 110, 10, 340, 18 * len(sec)
    bc.data = [list(sec["Return %"][::-1])]; bc.categoryAxis.categoryNames = list(sec["Sector"][::-1])
    bc.categoryAxis.labels.fontSize = bc.valueAxis.labels.fontSize = 8; bc.bars[0].fillColor = NAVY
    d.add(bc); s += [Paragraph("Sector Performance", H), d]
    s.append(_tbl([["Sector", "Return", "Avg RSI", "Volatility"]] + [[r["Sector"], f(r["Return %"]), f'{r["RSI"]:.1f}', f'{r["Volatility %"]:.1f}%'] for r in sec.to_dict("records")]))
    m = result["metrics"].sort_values("Return %", ascending=False)
    cols = ["Ticker", "Return", "RSI", "Signal"]
    row = lambda r: [r["Ticker"], f(r["Return %"]), f'{r["RSI"]:.1f}', r["Signal"]]
    s += [Paragraph("Top 10 Performers", H), _tbl([cols] + [row(r) for r in m.head(10).to_dict("records")]),
          Paragraph("Bottom 5", H), _tbl([cols] + [row(r) for r in m.tail(5).to_dict("records")]),
          Paragraph("AI Commentary", H)] + _md(result["commentary"])
    s += [Spacer(1, 10), Paragraph("<font size=7 color='#64748B'>Generated from delayed public data (yfinance). Educational only; not investment advice.</font>", B)]
    doc.build(s); return buf.getvalue()
