#!/usr/bin/env python3
"""
图片处理 - 优化国内访问速度
"""

import os
from pathlib import Path


def is_external_image(url):
    """判断是否为外部图片"""
    return url.startswith("http://") or url.startswith("https://")


def get_image_proxy_url(url):
    """
    获取图片代理URL
    使用国内可访问的代理服务，确保图片能正常显示
    """
    if not url:
        return ""
    
    # 如果图片来自外部CDN，使用代理加速
    # 方案1: 使用 wsrv.nl (Images.weserv.nl) 代理
    # 方案2: 使用 jsDelivr CDN
    # 方案3: 本地下载并压缩
    
    # 这里推荐方案1：Images.weserv.nl 支持国内访问
    weserv_url = f"https://images.weserv.nl/?url={url}"
    return weserv_url


def download_image(url, save_path):
    """
    下载图片到本地
    用于减少外部依赖，加快页面加载
    """
    import urllib.request
    
    try:
        # 添加User-Agent避免被拒
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(data)
            
            return True
    except Exception as e:
        print(f"下载图片失败: {url} - {e}")
        return False


def optimize_image_urls(items):
    """
    优化列表中所有图片URL
    使其在国内可以正常访问
    """
    for item in items:
        for key in ["thumbnail", "cover", "image"]:
            if key in item and item[key]:
                item[key] = get_image_proxy_url(item[key])
        
        # 处理images列表
        if "images" in item and isinstance(item["images"], list):
            item["images"] = [get_image_proxy_url(img) for img in item["images"]]