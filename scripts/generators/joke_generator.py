#!/usr/bin/env python3
"""
笑话/搞笑内容生成器
按"每个平台"产出各自的搞笑/笑话 Top10（第二类报告）

合规原则（最高优先）:
1. 严格排除严肃/灾难/伤亡/时政/违法犯罪新闻（绝不与这类话题配笑话）
2. 优先采用各平台"真实的、非新闻的轻松用户内容"直接作为搞笑内容（is_real=True）
   —— 小红书等平台的信息流本身就是用户的趣事/段子分享
3. 兜底段子（is_real=False）仅在命中"轻松生活类白名单"时生成，绝不硬凑
4. 某平台今日无任何可娱乐化内容时，如实标注"今日无搞笑数据"（不造假）
"""

import random

from utils.sensitive import is_serious, is_funny, NEWSISH_KEYWORDS


# 段子模板（仅用在命中"轻松生活类白名单"的话题上）
JOKE_TEMPLATES = [
    {
        "type": "吐槽",
        "template": "{topic}？程序员听到都笑了，因为{comment}",
        "comments": [
            "他们的代码早就这么写了",
            "这比npm install还快",
            "其实就是个Hello World的变体",
            "这在我眼里就是一行if else的事",
            "我的数据库里天天都是这个"
        ]
    },
    {
        "type": "冷幽默",
        "template": "关于{topic}，我只想说：{comment}",
        "comments": [
            "不是所有热点都值得追，就像不是所有bug都有价值修复",
            "这热度像极了我加的班，说没就没",
            "别人在追热点，我在追deadline",
            "热点会过期，段子不会",
            "你刷到的不是热点，是时间的流逝"
        ]
    },
    {
        "type": "生活",
        "template": "{topic}？{comment}",
        "comments": [
            "我昨天刚跟我妈讨论过这个话题，她说是时候找对象了",
            "我室友说这个话题能火，因为他昨天刚买了一样的",
            "我一个i人看到这种话题只想点个赞然后继续躺平",
            "这大概就是生活的乐趣吧",
        ]
    }
]


# ------------------------------------------------------------------
# 正向白名单：可娱乐化的轻松生活类内容
# 兜底段子只允许在这些范围内生成；不在范围内的新闻/时事一律不配段子
# ------------------------------------------------------------------
FUN_LIFESTYLE_KEYWORDS = [
    "生活", "日常", "心情", "心态", "上班", "打工人", "摸鱼", "刷到",
    "工作", "学习", "考试", "作业", "老师", "同学",
    "恋爱", "对象", "男朋友", "女朋友", "结婚", "相亲", "分手", "前任",
    "爸妈", "妈妈", "爸爸", "家庭", "孩子", "老人",
    "美食", "吃", "奶茶", "火锅", "外卖", "零食", "咖啡", "蛋糕",
    "猫", "狗", "宠物", "萌宠", "撸猫", "铲屎",
    "穿搭", "衣服", "鞋子", "包包", "口红", "化妆", "护肤",
    "旅行", "旅游", "景点", "拍照", "打卡", "逛街",
    "游戏", "手机", "电脑", "app", "软件",
    "熬夜", "失眠", "起床", "洗澡", "在家", "宅",
]

# 真实轻松/搞笑内容的"生活化"信号词
# 命中这些且非新闻的，可视为真实搞笑/趣事内容（is_real=True）
FUN_POST_SIGNALS = [
    "！！！", "！！", "？！", "哈哈", "哈哈哈哈", "笑死", "笑不活", "爆笑",
    "好玩", "有趣", "离谱", "上头", "尴尬", "可爱", "谁懂", "家人们",
    "😂", "😄", "🤣", "🙈", "救命",
]

# 明显属于新闻/资讯/通告的话题特征（用于否定判断）
NEWS_MARKERS = [
    "实拍", "报道", "现场", "通报", "新闻", "新增", "官方", "发布", "声明",
    "赛事", "决赛", "世界杯", "奥运", "赛况", "比分",
]


def _is_fun_post(title):
    """判断是否为"真实的轻松/搞笑用户内容"（非新闻时事）"""
    if not title or is_serious(title):
        return False
    low = title.lower()
    if _is_newsish(title, low):
        return False
    # 优先看显性搞笑关键词
    if is_funny(title):
        return True
    # 其次看生活化/趣味信号
    return any(s in title for s in FUN_POST_SIGNALS)


def _is_newsish(title, low):
    """判断是否为新闻/时事/政策/外文等不适合当搞笑内容的话题"""
    for kw in NEWSISH_KEYWORDS:
        if kw in title:
            return True
    for kw in ("president", "speech", "election", "tariff", "policy",
               "earthquake", "flood", "death", "killed", "war", "ipo",
               "fw26", "press", "closes", "forecast"):
        if kw in low:
            return True
    for mk in NEWS_MARKERS:
        if mk in title:
            return True
    return False


def _is_lightweight(title):
    """是否允许生成兜底段子（需命中轻松生活白名单且非新闻）"""
    if not title or is_serious(title):
        return False
    if _is_newsish(title, title.lower()):
        return False
    return any(kw in title for kw in FUN_LIFESTYLE_KEYWORDS)


def build_platform_funny(platform, items, top_n=10):
    """
    构建单个平台的搞笑/笑话 Top10
    返回: list of {"title","text","type","platform","is_real","rank"}
    """
    if not items:
        return []

    real_items = []
    fallback = []

    for it in items:
        title = it.get("title") or it.get("topic") or ""
        if not title or is_serious(title):
            continue
        if _is_fun_post(title):
            real_items.append(it)
        elif _is_lightweight(title):
            fallback.append(it)

    result = []

    # 1. 真实轻松/搞笑内容优先（标题即趣事，直接展示）
    for it in real_items[:top_n]:
        title = it.get("title", "")
        result.append({
            "title": title,
            "text": title,
            "type": "搞笑/趣事",
            "platform": platform,
            "url": it.get("url", ""),
            "is_real": True,
            "rank": 0,
        })

    # 2. 命中轻松生活白名单的话题才生成兜底段子（少量、不硬凑）
    need = top_n - len(result)
    if need > 0 and fallback:
        random.shuffle(fallback)
        for it in fallback[:need]:
            title = it.get("title", "")
            result.append({
                "title": title,
                "text": _generate_joke_text(title),
                "type": "段子",
                "platform": platform,
                "url": it.get("url", ""),
                "is_real": False,
                "rank": 0,
            })

    for i, item in enumerate(result, 1):
        item["rank"] = i
    return result[:top_n]


def _generate_joke_text(topic):
    """为轻松生活话题生成兜底段子"""
    t = random.choice(JOKE_TEMPLATES)
    comment = random.choice(t["comments"])
    try:
        return t["template"].format(topic=topic, comment=comment)
    except Exception:
        return f"关于{topic}，我只想说：懂的都懂 😄"


def build_funny_report(data, top_n=10):
    """构建"每个平台搞笑/笑话 Top10"整份报告"""
    platforms = data.get("platforms", {})
    report = {}
    for platform, items in platforms.items():
        report[platform] = build_platform_funny(platform, items, top_n=top_n)
    return report