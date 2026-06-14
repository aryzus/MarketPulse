from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import datetime

TEAL = HexColor('#00d4aa')
NAVY = HexColor('#0a0e1a')
DARK = HexColor('#0d1117')
GREEN = HexColor('#2ecc71')
RED = HexColor('#e74c3c')
GRAY = HexColor('#6b7280')
LIGHT = HexColor('#e2e8f0')

def generate_report(market_data, ai_insight, period, filename="data/market_report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=24,
        fontName='Helvetica-Bold',
        textColor=TEAL,
        spaceAfter=4,
        alignment=TA_LEFT
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=GRAY,
        spaceAfter=20,
        alignment=TA_LEFT
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        fontName='Helvetica-Bold',
        textColor=TEAL,
        spaceBefore=16,
        spaceAfter=8,
        borderPad=4
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=HexColor('#2d3748'),
        spaceAfter=4,
        leading=14
    )
    insight_style = ParagraphStyle(
        'Insight',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica',
        textColor=HexColor('#1a202c'),
        spaceAfter=4,
        leading=16,
        leftIndent=8
    )

    now = datetime.datetime.now()

    elements.append(Paragraph("India Stock Market AI Agent", title_style))
    elements.append(Paragraph(
        f"Market Analysis Report · {now.strftime('%B %d, %Y')} · Period: {period}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=2, color=TEAL, spaceAfter=16))

    elements.append(Paragraph("Market Indices", section_style))
    indices = market_data.get('indices', {})
    if indices:
        index_data = [['Index', 'Return (%)', 'Signal']]
        for name, ret in indices.items():
            signal = '▲ Bullish' if ret > 0 else '▼ Bearish'
            index_data.append([name, f"{ret:+.2f}%", signal])

        index_table = Table(index_data, colWidths=[2.8*inch, 1.5*inch, 1.5*inch])
        index_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), TEAL),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8fafc'), white]),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#e2e8f0')),
            ('ROWHEIGHT', (0,0), (-1,-1), 22),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(index_table)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Sector Performance", section_style))
    sectors = market_data.get('sectors', {})
    if sectors:
        sorted_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)
        sector_data = [['Sector', 'Return (%)', 'Performance']]
        for sector, ret in sorted_sectors:
            perf = '🟢 Outperforming' if ret > 0 else '🔴 Underperforming'
            sector_data.append([sector, f"{ret:+.2f}%", perf])

        sector_table = Table(sector_data, colWidths=[2*inch, 1.5*inch, 2.3*inch])
        sector_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), TEAL),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8fafc'), white]),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#e2e8f0')),
            ('ROWHEIGHT', (0,0), (-1,-1), 22),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(sector_table)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("Key Stocks Analysis", section_style))
    stocks = market_data.get('stocks', {})
    if stocks:
        stock_data = [['Stock', 'Price (₹)', 'Return (%)', 'RSI', 'Signal']]
        for name, info in stocks.items():
            ret = info.get('total_return', 0)
            rsi = info.get('rsi', 'N/A')
            price = info.get('current_price', 'N/A')
            if rsi and rsi != 'N/A':
                if rsi < 30:
                    signal = 'Oversold — Buy'
                elif rsi > 70:
                    signal = 'Overbought — Sell'
                else:
                    signal = 'Neutral — Hold'
            else:
                signal = 'N/A'
            stock_data.append([
                name,
                f"₹{price}",
                f"{ret:+.2f}%",
                str(rsi),
                signal
            ])

        stock_table = Table(
            stock_data,
            colWidths=[1.6*inch, 1*inch, 1*inch, 0.7*inch, 1.5*inch]
        )
        stock_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), NAVY),
            ('TEXTCOLOR', (0,0), (-1,0), TEAL),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,1), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#f8fafc'), white]),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#e2e8f0')),
            ('ROWHEIGHT', (0,0), (-1,-1), 20),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elements.append(stock_table)
        elements.append(Spacer(1, 12))

    elements.append(Paragraph("AI Agent Analysis", section_style))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=TEAL, spaceAfter=8))

    if ai_insight:
        clean_lines = []
        for line in ai_insight.split('\n'):
            line = line.strip()
            if not line:
                continue
            line = line.replace('**', '').replace('##', '').replace('###', '').replace('*', '•')
            if line.startswith('#'):
                line = line.lstrip('#').strip()
                clean_lines.append(('heading', line))
            else:
                clean_lines.append(('body', line))

        for style_type, line in clean_lines:
            if style_type == 'heading':
                elements.append(Paragraph(line, ParagraphStyle(
                    'InsightHeading',
                    parent=styles['Normal'],
                    fontSize=10,
                    fontName='Helvetica-Bold',
                    textColor=HexColor('#1a202c'),
                    spaceBefore=8,
                    spaceAfter=4
                )))
            else:
                elements.append(Paragraph(line, insight_style))

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1, color=GRAY, spaceAfter=8))
    elements.append(Paragraph(
        f"Generated by India Stock Market AI Agent · {now.strftime('%Y-%m-%d %H:%M')} IST · Data source: NSE/BSE via Yahoo Finance",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=7,
            fontName='Helvetica',
            textColor=GRAY,
            alignment=TA_CENTER
        )
    ))

    doc.build(elements)
    print(f"Report saved to {filename}")
    return filename

if __name__ == "__main__":
    sample_data = {
        'indices': {'Nifty 50': 1.04, 'Sensex': 1.30, 'Nifty Bank': 6.09, 'Nifty IT': -1.56},
        'sectors': {'Banking': 5.82, 'Pharma': 1.70, 'Finance': 0.33, 'Auto': -0.62, 'Metals': -1.01, 'IT': -2.05, 'FMCG': -5.52, 'Energy': -6.21},
        'stocks': {
            'ICICI Bank': {'current_price': 1340.8, 'total_return': 8.10, 'rsi': 62.08},
            'TCS': {'current_price': 2161.4, 'total_return': -4.76, 'rsi': 37.69},
            'Reliance Industries': {'current_price': 1293, 'total_return': -4.77, 'rsi': 27.11},
        }
    }
    sample_insight = """
    Banking sector leads with +5.82% return driven by ICICI Bank and SBI.
    Energy sector underperforms at -6.21% due to global crude price pressure.
    Recommendation: Buy banking stocks, avoid energy sector short term.
    """
    generate_report(sample_data, sample_insight, "1mo")
    print("Test report generated!")