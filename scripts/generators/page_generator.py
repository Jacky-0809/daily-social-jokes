#!/usr/bin/env python3
"""
页面生成器
生成两类图文报告页面:
1. 热点汇总榜（各平台Top10聚合去重后的统一热点榜）
2. 笑话/搞笑榜（每个平台各自的搞笑Top10）
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from html import escape
from urllib.parse import quote


def _platform_name(p):
    """平台中文名"""
    names = {
        "x": "X",
        "youtube": "YouTube",
        "xiaohongshu": "小红书",
        "douyin": "抖音",
        "kuaishou": "快手"
    }
    return names.get(p, p)


def _platform_color(p):
    """平台颜色"""
    colors = {
        "x": "#1da1f2",
        "youtube": "#ff0000",
        "xiaohongshu": "#e83e4c",
        "douyin": "#25f4ee",
        "kuaishou": "#ff4906"
    }
    return colors.get(p, "#666666")


def _medal(rank):
    return "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"{rank}"))


def _fmt_hot(val):
    """格式化热度值（万/亿）"""
    if not val:
        return ""
    try:
        v = float(val)
    except (TypeError, ValueError):
        return str(val)
    if v >= 100000000:
        return f"{v/100000000:.1f}亿"
    if v >= 10000:
        return f"{v/10000:.1f}万"
    return str(int(v))


# ============ 第一类：热点汇总榜 ============
def _build_hot_section(hot_list):
    """构建热点汇总榜HTML"""
    if not hot_list:
        return '<section class="platform-section"><h2 style="border-left:4px solid #2d3436;">🔥 热点汇总</h2><p>今日暂无热点数据</p></section>'

    parts = [
        '<section class="platform-section">',
        '    <h2 style="border-left: 4px solid #2d3436;">🔥 今日热点汇总榜</h2>',
        '    <p class="section-sub">聚合多平台Top10，去重排序 · 已排除灾难/伤亡类敏感新闻</p>',
        '    <div class="card-list">',
    ]
    for item in hot_list:
        title = escape(str(item.get("title", "")))
        desc = escape(str(item.get("desc", "") or item.get("description", "")))
        author = escape(str(item.get("author", "")))
        hot = item.get("hot", 0)
        url = item.get("url", "")
        sources = item.get("platforms", [item.get("platform", "")])
        source_tags = "".join(
            f'<span class="tag" style="color:{_platform_color(p)}">{_platform_name(p)}</span>'
            for p in sources
        )
        heat = f'<span class="heat">🔥 {_fmt_hot(hot)}</span>' if hot else ""

        parts.extend([
            f'        <div class="card">',
            f'            <div class="card-rank">{_medal(item.get("rank", 1))}</div>',
            f'            <div class="card-body">',
            f'                <h3><a href="{escape(url)}" target="_blank">{title}</a></h3>',
            (f'                <p class="desc">{desc}</p>' if desc else ''),
            f'                <div class="meta">'
            f'                    <span>{source_tags}</span>'
            f'                    {heat}'
            f'                    {"<span>👤 " + author + "</span>" if author else ""}'
            f'                </div>'
            f'            </div>'
            f'        </div>',
        ])
    parts.append('    </div></section>')
    return "\n".join(parts)


# ============ 第二类：每个平台的笑话/搞笑Top10 ============
def _build_platform_funny_section(platform, items):
    """构建单个平台的笑话/搞笑 Top10"""
    pname = _platform_name(platform)
    pcolor = _platform_color(platform)

    if not items:
        return (
            f'<section class="platform-section funny-section">'
            f'<h2 style="border-left:4px solid {pcolor};">😂 {pname} 笑话/搞笑榜</h2>'
            f'<p class="empty-hint">今日 {pname} 无可娱乐化的搞笑内容（已排除伤亡/时政新闻）</p>'
            f'</section>'
        )

    parts = [
        f'<section class="platform-section funny-section">',
        f'    <h2 style="border-left: 4px solid {pcolor};">😂 {pname} 笑话/搞笑 Top10</h2>',
        '    <div class="joke-list">',
    ]
    for item in items:
        text = escape(str(item.get("text", "")))
        title = escape(str(item.get("title", "")))
        ptype = escape(str(item.get("type", "搞笑内容")))
        url = item.get("url", "")
        real_badge = '<span class="tag tag-real">真实内容</span>' if item.get("is_real") else '<span class="tag tag-gen">段子</span>'

        title_html = f'<div class="joke-title"><a href="{escape(url)}" target="_blank">{title}</a></div>' if title else ""
        parts.extend([
            f'        <div class="joke-card">',
            f'            <div class="joke-number">{item.get("rank", 1)}</div>',
            f'            <div class="joke-content">',
            title_html,
            f'                <p class="joke-text">{text}</p>',
            f'                <div class="joke-tags">'
            f'                    <span class="tag">{ptype}</span>'
            f'                    {real_badge}'
            f'                </div>'
            f'            </div>'
            f'        </div>',
        ])
    parts.append('    </div></section>')
    return "\n".join(parts)


def _build_funny_report(funny_report):
    """构建整份笑话/搞笑榜（按平台分节）"""
    sections = []
    order = ["xiaohongshu", "douyin", "kuaishou", "x", "youtube"]
    for platform in order:
        if platform in funny_report:
            sections.append(_build_platform_funny_section(platform, funny_report[platform]))
    # 任何未列出的平台
    for platform in funny_report:
        if platform not in order:
            sections.append(_build_platform_funny_section(platform, funny_report[platform]))
    return "\n".join(sections) if sections else "<p>今日无搞笑数据</p>"


# ============ 组装整页 ============
def generate_daily_page(data, hot_list, funny_report, config):
    """生成每日双报告页面"""
    date_str = data["date"]
    local_date = datetime.now().strftime("%Y-%m-%d %H:%M")

    hot_html = _build_hot_section(hot_list)
    funny_html = _build_funny_report(funny_report)

    # 数据真实性标注（诚实验证）
    mode_notes = []
    for platform, items in data.get("platforms", {}).items():
        if platform == "youtube":
            source = data.get("_source_flags", {}).get("youtube", "mock")
            if source == "mock":
                mode_notes.append("YouTube 为示例数据（未配置API Key）")

    note_html = " · ".join(mode_notes)

    page_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="每日社交平台热点与笑话汇总">
    <title>每日热点与笑话榜 {date_str}</title>
    <link rel="stylesheet" href="../../css/style.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1>📊 每日社交平台热点与笑话榜</h1>
            <p class="subtitle">X · YouTube · 小红书 · 抖音 · 快手 | {date_str}</p>
            {('<p class="note">'+note_html+'</p>') if note_html else ''}
        </div>
    </header>

    <main class="container">
        <div class="date-badge">📅 {local_date} · 每日更新</div>

        {hot_html}

        <div class="report-divider"></div>

        {funny_html}

        <footer class="site-footer">
            <p>数据来源：各平台公开数据 · 内容仅供娱乐参考 · 已自动排除伤亡/时政类敏感新闻</p>
            <p><a href="../../index.html">返回首页</a> · <a href="../../rss.xml">RSS订阅</a></p>
        </footer>
    </main>
</body>
</html>
"""
    output_dir = Path(__file__).parent.parent.parent / "site" / config.get("output_path", "Joke") / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "index.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(page_html)

    update_index(data)
    update_rss(data, funny_report)
    print(f"页面已生成: {output_file}")


def update_index(data):
    """更新首页归档"""
    date_str = data["date"]
    site_dir = Path(__file__).parent.parent.parent / "site"
    joke_dir = site_dir / "Joke"
    dates = []
    if joke_dir.exists():
        for d in joke_dir.iterdir():
            if d.is_dir():
                dates.append(d.name)
    dates.sort(reverse=True)
    date_links = "".join(f'<li><a href="Joke/{d}/">{d}</a></li>' for d in dates) or "<li>暂无数据</li>"

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日社交平台热点与笑话榜</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header class="site-header">
        <div class="container">
            <h1>📊 每日社交平台热点与笑话榜</h1>
            <p class="subtitle">X · YouTube · 小红书 · 抖音 · 快手</p>
        </div>
    </header>
    <main class="container">
        <section>
            <h2>📅 每日归档</h2>
            <ul class="archive-list">{date_links}</ul>
        </section>
        <footer class="site-footer">
            <p>数据来源：各平台公开数据 · 内容仅供娱乐参考</p>
            <p><a href="rss.xml">RSS订阅</a></p>
        </footer>
    </main>
</body>
</html>
"""
    index_file = site_dir / "index.html"
    with open(index_file, "w", encoding="utf-8") as f:
        f.write(index_html)
    print(f"首页已更新: {index_file}")


def update_rss(data, funny_report):
    """更新RSS feed（仅收录非严肃的真实搞笑内容）"""
    date_str = data["date"]
    rss_items = []
    for platform, items in funny_report.items():
        for joke in items[:5]:
            if not joke.get("is_real"):
                continue  # RSS只收真实搞笑内容，段子不入feed
            title = escape(joke.get("title", "搞笑内容"))
            desc = escape(joke.get("text", ""))
            rss_items.append(f"""
    <item>
        <title>[{_platform_name(platform)}] {title}</title>
        <link>{escape(joke.get('url', ''))}</link>
        <description>{desc}</description>
        <pubDate>{data['fetched_at']}</pubDate>
        <guid>joke-{date_str}-{platform}-{joke.get('rank')}</guid>
    </item>""")

    rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>每日社交平台热点与笑话榜</title>
        <link>https://yourusername.github.io/daily-social-jokes/</link>
        <description>每日社交平台热点与笑话汇总</description>
        <language>zh-CN</language>
        <lastBuildDate>{data['fetched_at']}</lastBuildDate>
        {''.join(rss_items)}
    </channel>
</rss>
"""
    rss_file = Path(__file__).parent.parent.parent / "site" / "rss.xml"
    with open(rss_file, "w", encoding="utf-8") as f:
        f.write(rss_xml)
    print(f"RSS已更新: {rss_file}")