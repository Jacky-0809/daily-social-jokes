#!/usr/bin/env python3
"""
X(Twitter)热门话题爬虫 - 免登录真实数据
通过Trends24.in聚合站点获取X全球热门趋势
参考: https://github.com/azharimm/twitter-trends-api
"""

import re
from datetime import datetime, timezone
from urllib.parse import unquote

import requests

from utils.proxy import get_headers


def scrape_x_trending(top_n=10):
    """
    抓取X全球热门话题
    逻辑: GET trends24.in -> 解析 trend-card__list -> 提取top10
    """
    session = requests.Session()
    session.headers.update(get_headers())

    try:
        resp = session.get("https://trends24.in/", timeout=25)
        resp.raise_for_status()
        # 使用utf-8（含中文/日文/emoji）
        resp.encoding = "utf-8"
        html = resp.text
    except Exception as e:
        print(f"X趋势请求失败: {e}")
        return []

    # 提取最新快照的趋势列表
    i = html.find('<ol class=trend-card__list>')
    if i == -1:
        print("Trends24页面结构变更，未找到趋势列表")
        return []

    block = html[i: html.find('</ol>', i)]
    items = re.findall(
        r'<a href="https://twitter\.com/search\?q=([^"]+)" class=trend-link>([^<]+)</a>',
        block,
    )

    # 提取时间戳
    timestamp = None
    m = re.search(r'<h3 class=title data-timestamp=(\d+\.?\d*)>', html)
    if m:
        try:
            timestamp = datetime.fromtimestamp(
                float(m.group(1)), timezone.utc
            ).isoformat()
        except Exception:
            pass

    result = []
    for rank, (query, topic) in enumerate(items[:top_n], 1):
        try:
            clean_topic = unquote(topic)
        except Exception:
            clean_topic = topic
        result.append({
            "rank": rank,
            "title": clean_topic,
            "description": "",
            "query": query,
            "timestamp": timestamp or "",
            "url": f"https://twitter.com/search?q={query}",
            "platform": "x",
        })

    return result