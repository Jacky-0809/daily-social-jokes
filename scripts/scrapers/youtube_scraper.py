#!/usr/bin/env python3
"""
YouTube热门视频爬虫
真实数据需要 YOUTUBE_API_KEY 环境变量，未配置时返回模拟数据
"""

import json
import os

import requests

from utils.proxy import get_headers


def scrape_youtube_trending(top_n=10):
    """
    抓取YouTube热门视频
    使用YouTube Data API v3 chart=mostPopular
    """
    api_key = os.getenv("YOUTUBE_API_KEY", "")

    if not api_key:
        print("警告: 未设置 YOUTUBE_API_KEY 环境变量，返回模拟数据")
        return _mock_data(top_n)

    url = (
        "https://www.googleapis.com/youtube/v3/videos"
        f"?part=snippet,statistics&chart=mostPopular&maxResults={top_n}"
        f"&key={api_key}"
    )

    try:
        resp = requests.get(url, headers=get_headers(), timeout=25)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"YouTube API调用失败: {e}")
        return _mock_data(top_n)

    items = data.get("items", [])
    result = []
    for i, item in enumerate(items, 1):
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        video_id = item.get("id", "")
        result.append({
            "rank": i,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "author": snippet.get("channelTitle", ""),
            "views": stats.get("viewCount", "0"),
            "likes": stats.get("likeCount", "0"),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "platform": "youtube",
        })

    return result


def _mock_data(top_n=10):
    """返回模拟数据（未配置API Key时）"""
    return [
        {
            "rank": i + 1,
            "title": f"YouTube热门视频 {i + 1}",
            "description": f"这是第 {i + 1} 个热门视频的描述",
            "author": f"频道 {i + 1}",
            "views": f"{1000000 - i * 100000}",
            "likes": f"{50000 - i * 5000}",
            "url": f"https://www.youtube.com/watch?v=video{i+1}",
            "thumbnail": f"https://i.ytimg.com/vi/video{i+1}/hqdefault.jpg",
            "platform": "youtube",
        }
        for i in range(top_n)
    ]