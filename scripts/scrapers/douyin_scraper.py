#!/usr/bin/env python3
"""
抖音热榜爬虫 - 免登录真实数据
参考: https://github.com/imsyy/DailyHotApi/src/routes/douyin.ts
"""

import json
import re

import requests

from utils.proxy import get_headers


def scrape_douyin(top_n=10):
    """
    抓取抖音热榜
    逻辑:
    1. 获取临时cookie passport_csrf_token
    2. 调用官方web接口获取热榜
    """
    session = requests.Session()
    session.headers.update(get_headers())

    # Step 1: 获取临时cookie (部分环境可跳过)
    csrf_token = ""
    try:
        resp = session.get(
            "https://www.douyin.com/passport/general/login_guiding_strategy/?aid=6383",
            timeout=20,
        )
        set_cookie = resp.headers.get("set-cookie", "")
        m = re.search(r"passport_csrf_token=([^;]+)", set_cookie)
        if m:
            csrf_token = m.group(1)
    except Exception:
        pass

    # Step 2: 请求热榜接口
    url = (
        "https://www.douyin.com/aweme/v1/web/hot/search/list/"
        "?device_platform=webapp&aid=6383&channel=channel_pc_web&detail_list=1"
    )
    headers = {"Referer": "https://www.douyin.com/"}
    if csrf_token:
        headers["Cookie"] = f"passport_csrf_token={csrf_token}"

    try:
        resp = session.get(url, headers=headers, timeout=25)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"抖音热榜请求失败: {e}")
        return []

    word_list = data.get("data", {}).get("word_list", [])
    items = []
    for i, v in enumerate(word_list[:top_n]):
        # 事件的 word 本身就是标题/话题；label 是类目标记非描述，故 description 置空
        items.append({
            "rank": i + 1,
            "title": v.get("word", ""),
            "description": "",
            "sentence_id": v.get("sentence_id", ""),
            "hot": v.get("hot_value", 0),   # 真实热度值
            "event_time": v.get("event_time", ""),
            "url": f"https://www.douyin.com/hot/{v.get('sentence_id','')}",
            "platform": "douyin",
        })
    return items