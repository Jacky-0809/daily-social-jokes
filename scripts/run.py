#!/usr/bin/env python3
"""
每日社交平台热门话题与笑话抓取主控脚本
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from scrapers.x_scraper import scrape_x_trending
from scrapers.youtube_scraper import scrape_youtube_trending
from scrapers.xiaohongshu_scraper import scrape_xiaohongshu
from scrapers.douyin_scraper import scrape_douyin
from scrapers.kuaishou_scraper import scrape_kuaishou
from generators.hot_aggregator import aggregate_hot
from generators.joke_generator import build_funny_report
from generators.page_generator import generate_daily_page


def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent.parent / "config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    else:
        # 默认配置
        return {
            "platforms": ["x", "youtube", "xiaohongshu", "douyin", "kuaishou"],
            "top_n": 10,
            "output_path": "Joke",
            "use_proxy": False,
            "image_quality": "medium"
        }


def scrape_all_platforms(config):
    """抓取所有平台的热门内容"""
    all_data = {}
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    scrapers = {
        "x": scrape_x_trending,
        "youtube": scrape_youtube_trending,
        "xiaohongshu": scrape_xiaohongshu,
        "douyin": scrape_douyin,
        "kuaishou": scrape_kuaishou
    }
    
    for platform in config["platforms"]:
        if platform in scrapers:
            print(f"正在抓取 {platform}...")
            try:
                data = scrapers[platform](top_n=config["top_n"])
                all_data[platform] = data
                print(f"  成功抓取 {len(data)} 条数据")
            except Exception as e:
                print(f"  抓取 {platform} 失败: {e}")
                all_data[platform] = []
    
    return {
        "date": date_str,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "platforms": all_data
    }


def main():
    """主函数"""
    print("=== 每日社交平台热点与笑话抓取 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 加载配置
    config = load_config()
    print(f"配置: {json.dumps(config, ensure_ascii=False, indent=2)}")
    
    # 抓取数据
    print("\n--- 开始抓取数据 ---")
    data = scrape_all_platforms(config)

    # 记录各平台数据真实性来源（诚实标注，假数据不冒充）
    flags = {}
    for platform, items in data.get("platforms", {}).items():
        if platform == "youtube":
            title0 = items[0].get("title", "") if items else ""
            flags["youtube"] = "mock" if title0.startswith("YouTube热门视频") else "real"
    data["_source_flags"] = flags
    
    # 保存原始数据
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    data_file = data_dir / f"{data['date']}.json"
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n数据已保存到: {data_file}")
    
    # 第一类：热点汇总
    print("\n--- 生成热点汇总榜 ---")
    hot_list = aggregate_hot(data, top_n=config["top_n"])
    print(f"热点汇总共 {len(hot_list)} 条（已排除敏感新闻）")

    # 第二类：每个平台的笑话/搞笑Top10
    print("\n--- 生成每个平台的笑话/搞笑榜 ---")
    funny_report = build_funny_report(data, top_n=config["top_n"])
    for platform, items in funny_report.items():
        n_real = sum(1 for it in items if it.get("is_real"))
        print(f"  {platform}: {len(items)} 条（真实搞笑{n_real}含段子补充）")
    
    # 生成页面
    print("\n--- 生成页面 ---")
    generate_daily_page(data, hot_list, funny_report, config)
    
    print(f"\n=== 完成 ===")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"访问页面: https://yourusername.github.io/daily-social-jokes/Joke/{data['date']}/")


if __name__ == "__main__":
    main()