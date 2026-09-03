#!/usr/bin/env python3
"""
PDF 报告生成器
把当日"热点汇总 + 每平台笑话榜"导出为 PDF（供邮件发送）
使用 reportlab + UnicodeCIDFont(STSong-Light) 支持中文，无需额外字体文件
"""

import json
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

from generators.hot_aggregator import aggregate_hot
from generators.joke_generator import build_funny_report

# 平台中文名与颜色
PLATFORM_NAMES = {
    "x": "X", "youtube": "YouTube", "xiaohongshu": "小红书",
    "douyin": "抖音", "kuaishou": "快手",
}
PLATFORM_COLORS = {
    "x": "#1da1f2", "youtube": "#ff0000", "xiaohongshu": "#e83e4c",
    "douyin": "#00c6fb", "kuaishou": "#ff4906",
}

# 每平台的展示顺序（根据当天实际有效内容动态决定也可）
ORDER = ["xiaohongshu", "douyin", "kuaishou", "x", "youtube"]

_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _fmt_hot(val):
    if not val:
        return ""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if v >= 1e8:
        return f"{v/1e8:.1f}亿"
    if v >= 1e4:
        return f"{v/1e4:.1f}万"
    return str(int(v))


def _register_font():
    """注册中文字体（CID字体，无需字体文件）"""
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass


def _build_pdf_story(data, hot_list, funny_report):
    """构造 PDF 内容流（list of Flowable）"""
    _register_font()
    styles = getSampleStyleSheet()

    def st(name, **kw):
        base = dict(fontName="STSong-Light", fontSize=10, leading=16)
        base.update(kw)
        return ParagraphStyle(name, **base, parent=styles["Normal"])

    title_st = st("t", fontSize=18, leading=26, alignment=1, spaceAfter=6)
    sub_st = st("s", fontSize=10, leading=16, alignment=1, textColor=colors.grey, spaceAfter=18)
    sec_st = st("sec", fontSize=14, leading=22, spaceBefore=16, spaceAfter=8, textColor=colors.HexColor("#667eea"))
    card_st = st("card", fontSize=10, leading=18)

    story = []
    date_str = data["date"]
    story.append(Paragraph("📊 每日社交平台热点与笑话报告", title_st))
    story.append(Paragraph(f"{date_str}  ·  X / YouTube / 小红书 / 抖音 / 快手", sub_st))

    # ===== 第一类：热点汇总 =====
    story.append(Paragraph("一、今日热点汇总榜", sec_st))
    if not hot_list:
        story.append(Paragraph("今日暂无热点数据", card_st))
    else:
        rows = [["#", "热点标题", "热度", "来源"]]
        for item in hot_list:
            rank = _MEDALS.get(item.get("rank", 0), str(item.get("rank", "")))
            sources = ",".join(PLATFORM_NAMES.get(s, s) for s in item.get("platforms", [item.get("platform", "")]))
            rows.append([
                rank,
                item.get("title", ""),
                _fmt_hot(item.get("hot", "")),
                sources,
            ])
        t = Table(rows, colWidths=[12 * mm, 95 * mm, 35 * mm, 40 * mm], repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#667eea")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6fa")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dfe6e9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    # ===== 第二类：每平台笑话榜 =====
    story.append(Paragraph("二、每个平台的笑话/搞笑 Top10", sec_st))
    for platform in ORDER:
        items = funny_report.get(platform, [])
        pname = PLATFORM_NAMES.get(platform, platform)
        sec_title = Paragraph(f"😂 {pname} 笑话/搞笑榜", st(
            "psec", fontSize=12, leading=18, spaceBefore=12, spaceAfter=4,
            textColor=colors.HexColor(PLATFORM_COLORS.get(platform, "#2d3436"))))
        story.append(sec_title)
        if not items:
            story.append(Paragraph("今日无可娱乐化的搞笑内容（已排除伤亡/时政新闻）", st(
                "empty", fontSize=10, leading=16, textColor=colors.grey)))
            continue
        for item in items:
            real_flag = "[真实内容]" if item.get("is_real") else "[段子]"
            rank = _MEDALS.get(item.get("rank", 0), str(item.get("rank", "")))
            line = f"{rank} {real_flag}  {item.get('text', '')}"
            story.append(Paragraph(line, card_st))

    generated_note = "示例数据" in _source_flags(data) and "（注：YouTube 为示例数据，未配置 API Key）" or ""
    if generated_note:
        story.append(Spacer(1, 10))
        story.append(Paragraph(generated_note, st("note", fontSize=8, textColor=colors.grey)))

    story.append(Spacer(1, 16))
    story.append(Paragraph("数据来源：各平台公开数据 · 内容仅供娱乐参考 · 已自动排除伤亡/时政类敏感新闻", st(
        "foot", fontSize=8, leading=12, textColor=colors.grey, alignment=1)))
    return story


def _source_flags(data):
    return data.get("_source_flags", {})


def generate_pdf(data, output_pdf):
    """
    生成 PDF 报告
    data: 当日数据 dict
    output_pdf: 输出 PDF 路径
    """
    hot_list = aggregate_hot(data, top_n=10)
    funny_report = build_funny_report(data, top_n=10)
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

    story = _build_pdf_story(data, hot_list, funny_report)
    doc = SimpleDocTemplate(
        output_pdf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=20 * mm, rightMargin=20 * mm,
        title=f"社交平台热点与笑话报告 {data['date']}",
        author="daily-social-jokes",
    )
    doc.build(story)
    return output_pdf


if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else "data/2026-09-03.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "report.pdf"
    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)
    generate_pdf(data, out)
    print(f"PDF已生成: {Path(out).resolve()}")
