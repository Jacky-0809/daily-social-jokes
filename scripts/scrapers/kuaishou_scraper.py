#!/usr/bin/env python3
"""
快手热榜爬虫 - 免登录真实数据
参考: https://github.com/imsyy/DailyHotApi/src/routes/kuaishou.ts
解析快手首页HTML内嵌的 __APOLLO_STATE__ JSON
"""

import json
import re

import requests

from utils.proxy import get_headers


APOLLO_STATE_PREFIX = "window.__APOLLO_STATE__="


def parse_chinese_number(text):
    """将'1336.9万'等中文数字转为整数"""
    if not text:
        return 0
    text = str(text).strip()
    num = 0.0
    unit = 1
    m = re.match(r"([\d.]+)", text)
    if m:
        num = float(m.group(1))
    if "亿" in text:
        unit = 100000000
    elif "万" in text:
        unit = 10000
    elif "千" in text:
        unit = 1000
    return int(num * unit)


def scrape_kuaishou(top_n=10, retries=3):
    """
    抓取快手热榜
    逻辑: GET首页 -> 解析 __APOLLO_STATE__ -> 提取 visionHotRank
    快手反爬严格，做多次重试和UA轮换
    """
    session = requests.Session()
    session.headers.update(get_headers())

    html = ""
    for attempt in range(retries):
        try:
            resp = session.get(
                "https://www.kuaishou.com/?isHome=1",
                timeout=25,
            )
            resp.raise_for_status()
            html = resp.text
            # 快手反爬会返回短JSON {"result":2,...}，此时无APOLLO数据
            if len(html) > 1000 and APOLLO_STATE_PREFIX in html:
                break
            # 反爬拦截，更换UA重试
            if attempt < retries - 1:
                session.headers["User-Agent"] = (
                    f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{120 + attempt}."
                    f"0.0.0 Safari/537.36"
                )
                import time
                time.sleep(2)
        except Exception as e:
            print(f"快手首页请求失败: {e}")
            if attempt < retries - 1:
                import time
                time.sleep(2)

    if not html or APOLLO_STATE_PREFIX not in html:
        print(f"快手反爬拦截或页面无数据 (len={len(html)})")
        return []

    # 提取 __APOLLO_STATE__ JSON
    start = html.find(APOLLO_STATE_PREFIX)
    if start == -1:
        print("快手页面结构变更，未找到 APOLLO_STATE")
        return []

    script_slice = html[start + len(APOLLO_STATE_PREFIX):]
    sentinel_a = script_slice.find(";(function(")
    sentinel_b = script_slice.find("</script>")

    if sentinel_a != -1 and sentinel_b != -1:
        cut = min(sentinel_a, sentinel_b)
    else:
        cut = max(sentinel_a, sentinel_b)
    if cut == -1:
        print("快手页面结构变更，未找到 APOLLO_STATE 结束标记")
        return []

    raw = script_slice[:cut].strip().rstrip(";")
    last_brace = raw.rfind("}")
    if last_brace != -1:
        raw = raw[:last_brace + 1]

    try:
        obj = json.loads(raw).get("defaultClient", {})
    except Exception as e:
        print(f"快手数据解析失败: {e}")
        return []

    # 获取热榜条目ID列表
    items = (
        obj.get('$ROOT_QUERY.visionHotRank({"page":"home"})', {}).get("items", [])
        or obj.get('$ROOT_QUERY.visionHotRank({"page":"home","platform":"web"})', {}).get("items", [])
    )

    result = []
    seen = set()
    for item in items[:top_n * 3]:
        hot_item = obj.get(item.get("id", ""), {})
        if not hot_item or hot_item.get("id") in seen:
            continue
        seen.add(hot_item.get("id"))
        photo_id = hot_item.get("photoIds", {}).get("json", [None])[0]
        name = hot_item.get("name", "")
        if not name:
            continue
        result.append({
            "title": name,
            "description": "",
            "author": "",
            "hot": parse_chinese_number(hot_item.get("hotValue", "")),
            "photo_id": photo_id or "",
            "cover": hot_item.get("poster", ""),
            "url": f"https://www.kuaishou.com/short-video/{photo_id}" if photo_id else "",
            "platform": "kuaishou",
        })
        if len(result) >= top_n:
            break

    # 补充rank
    for i, item in enumerate(result):
        item["rank"] = i + 1

    return result