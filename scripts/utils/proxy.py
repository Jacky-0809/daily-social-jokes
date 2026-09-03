#!/usr/bin/env python3
"""
代理与请求头工具
"""

import os


def get_proxy_config():
    """
    获取代理配置
    如果设置了PROXY_URL环境变量则使用，否则返回None（直连）
    """
    proxy = os.getenv("PROXY_URL", "")

    if proxy:
        return {
            "http": proxy,
            "https": proxy
        }

    return None


def get_headers(referer=None, desktop=True):
    """
    获取完整浏览器请求头
    模拟真实浏览器指纹，规避反爬
    """
    platform = "Macintosh; Intel Mac OS X 10_15_7" if desktop else "iPhone; CPU iPhone OS 16_0 like Mac OS X"
    headers = {
        "User-Agent": (
            f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    return headers