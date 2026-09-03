#!/usr/bin/env python3
"""
小红书热门笔记爬虫 - 免登录真实数据
抓取探索页 __INITIAL_STATE__ 信息流，按点赞数排序取Top
"""

import json
import re

import requests

from utils.proxy import get_headers


def scrape_xiaohongshu(top_n=10):
    """
    抓取小红书热门笔记
    逻辑: GET /explore -> 解析 __INITIAL_STATE__.feed.feeds -> 按点赞排序
    注意: 若返回空壳（需浏览器指纹），可设置 XHS_COOKIE 环境变量注入cookie
    """
    import os
    session = requests.Session()
    headers = get_headers()
    headers["Accept-Language"] = "zh-CN,zh;q=0.9"
    # 可选cookie
    cookie = os.getenv("XHS_COOKIE", "")
    if cookie:
        headers["Cookie"] = cookie
    session.headers.update(headers)

    try:
        resp = session.get("https://www.xiaohongshu.com/explore", timeout=25)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"小红书探索页请求失败: {e}")
        return []

    # 提取 __INITIAL_STATE__ 中的 feeds 数组
    idx = html.find("window.__INITIAL_STATE__=")
    if idx == -1:
        print("小红书页面结构变更，未找到 INITIAL_STATE")
        return []

    seg = html[idx + len("window.__INITIAL_STATE__="):]
    cut = seg.find("</script>")
    if cut == -1:
        cut = len(seg)
    raw = seg[:cut]

    # 定位 feeds 数组
    feeds_pos = raw.find('"feeds":')
    if feeds_pos == -1:
        # 尝试 __INITIAL_STATE__ 是对象的场景
        feeds_pos = raw.find("feeds:")
    if feeds_pos == -1:
        print("未找到 feeds 数据，可能返回空壳（需要cookie或浏览器）")
        return []

    # 用括号计数提取完整feeds数组
    arr_start = raw.find("[", feeds_pos)
    if arr_start == -1:
        return []

    depth = 0
    in_str = False
    esc = False
    k = arr_start
    while k < len(raw):
        c = raw[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    break
        k += 1

    arr_json = raw[arr_start:k + 1]
    try:
        feeds = json.loads(arr_json)
    except Exception as e:
        print(f"小红书feeds解析失败: {e}")
        return []

    # 提取每个笔记的详情并排序
    parsed = []
    for f in feeds:
        nc = f.get("noteCard", {}) or {}
        note_id = nc.get("noteId") or f.get("id", "")
        xsec_token = nc.get("xsecToken", "")
        title = nc.get("displayTitle", "") or nc.get("title", "")
        author = (nc.get("user", {}) or {}).get("nickname", "")
        interact = nc.get("interactInfo", {}) or {}
        likes = 0
        try:
            likes = int(interact.get("likedCount", 0) or 0)
        except (TypeError, ValueError):
            likes = 0

        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if xsec_token:
            url += f"?xsec_token={xsec_token}&xsec_source=pc_feed"

        parsed.append({
            "title": title,
            "description": "",
            "author": author,
            "likes": likes,
            "comments": int(interact.get("commentCount", 0) or 0),
            "note_id": note_id,
            "url": url,
            "platform": "xiaohongshu",
        })

    # 按点赞数降序排序取top
    parsed.sort(key=lambda x: x["likes"], reverse=True)
    for i, item in enumerate(parsed[:top_n]):
        item["rank"] = i + 1

    return parsed[:top_n]