#!/usr/bin/env python3
"""
热点汇总器
把各平台通用热门 top10 合并为一份"热点汇总榜"
按热度/点赞归一化后去重排序
"""

from utils.sensitive import exclude_serious, is_serious


def _get_hot_value(item):
    """取条目的热度值，做类型归一化"""
    for key in ("hot", "likes", "views", "hot_value", "hotValue"):
        v = item.get(key)
        if isinstance(v, (int, float)) and v:
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        if isinstance(v, str):
            # 处理 "1336.9万" 等中文数字
            try:
                if "万" in v:
                    return float(v.replace("万", "")) * 10000
                if "亿" in v:
                    return float(v.replace("亿", "")) * 100000000
                return float(v)
            except ValueError:
                continue
    return 0.0


def normalize_title(title):
    """归一化标题用于去重（去空白、去#、转小写）"""
    if not title:
        return ""
    t = str(title).lower()
    t = t.replace("#", "").replace(" ", "")
    return t


def aggregate_hot(data, top_n=10, include_serious_news=False):
    """
    聚合各平台热点为统一排行榜。
    include_serious_news=False 时（默认）剔除灾难/伤亡类严肃新闻，
    避免与后面的笑话内容混排造成冒犯。
    返回: [{title, hot, platforms:[..], url, platform(主来源)}, ...]
    """
    platforms = data.get("platforms", {})
    # 先用每平台各自的 rank 作为基础，再按热度二次排序
    candidates = []
    for platform, items in platforms.items():
        for it in items:
            title = it.get("title") or it.get("topic") or ""
            if not title:
                continue
            if not include_serious_news and is_serious(title):
                continue
            hot = _get_hot_value(it)
            candidates.append({
                "title": title,
                "desc": it.get("description", "") or it.get("desc", ""),
                "author": it.get("author", ""),
                "hot": hot,
                "url": it.get("url", ""),
                "platform": platform,
                # 平台rank做加权：rank高者同热度时优先
                "rank": it.get("rank", 99),
            })

    if not candidates:
        return []

    # 按热度降序，主排序依据热度；无热度时按平台rank
    candidates.sort(key=lambda x: (x["hot"] > 0, x["hot"], -x["rank"]), reverse=True)

    # 去重（同标题合并）
    merged = {}
    for c in candidates:
        key = normalize_title(c["title"])
        if not key:
            continue
        if key not in merged:
            c["platforms"] = [c["platform"]]
            merged[key] = c
        else:
            # 合并平台来源，保留较高热度
            existing = merged[key]
            if c["platform"] not in existing["platforms"]:
                existing["platforms"].append(c["platform"])
            if c["hot"] > existing["hot"]:
                existing["hot"] = c["hot"]

    result = sorted(merged.values(), key=lambda x: x["hot"], reverse=True)
    # 补充序号
    for i, item in enumerate(result[:top_n]):
        item["rank"] = i + 1
    return result[:top_n]