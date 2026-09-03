# 每日社交平台热门榜 🔥

自动抓取 X、YouTube、小红书、抖音、快手等社交平台每日热门Top10话题和笑话，生成图文混合版，发布到GitHub Pages。

## ✨ 特性

- 🤖 **全自动**：GitHub Actions 每日定时抓取，无需手动操作
- 😂 **笑话生成**：基于热门话题智能生成幽默段子
- 🎨 **图文混合**：响应式设计，支持图片展示
- 📡 **RSS 订阅**：支持 RSS 阅读器
- 🆓 **完全免费**：基于 GitHub Pages，零成本部署

## 🚀 快速开始

### 1. Fork 本项目

点击右上角 Fork 按钮，复制到你自己的账号下。

### 2. 启用 GitHub Pages

1. 进入仓库 Settings → Pages
2. Source 选择 "GitHub Actions"
3. 保存

### 3. 启用 Workflow 权限

1. 进入仓库 Settings → Actions → General
2. Workflow permissions 选择 "Read and write permissions"
3. 保存

### 4. 手动触发首次运行

1. 进入 Actions 标签页
2. 选择 "Daily Social Jokes" workflow
3. 点击 "Run workflow"

等待几分钟，你的网站就上线了！

## 📁 项目结构

```
daily-social-jokes/
├── .github/workflows/daily.yml   # GitHub Actions 自动运行配置
├── scripts/
│   ├── scrapers/
│   │   ├── x_scraper.py         # X/Twitter爬虫
│   │   ├── youtube_scraper.py   # YouTube爬虫
│   │   ├── xiaohongshu_scraper.py # 小红书爬虫
│   │   ├── douyin_scraper.py    # 抖音爬虫
│   │   └── kuaishou_scraper.py  # 快手爬虫
│   ├── generators/
│   │   ├── joke_generator.py    # 笑话生成器
│   │   └── page_generator.py    # 页面生成器
│   ├── utils/
│   │   ├── proxy.py             # 代理工具
│   │   └── image_handler.py     # 图片处理
│   └── run.py                   # 主控脚本
├── data/                         # 原始数据（JSON）
├── site/
│   ├── index.html
│   ├── css/style.css
│   ├── rss.xml
│   └── Joke/
│       └── 2026-01-01/          # 按日期目录
├── templates/                   # HTML模板
├── config.json                  # 配置文件
└── README.md
```

## 🌐 国内访问方案

GitHub Pages 使用 `${username}.github.io` 域名，在国内可能被访问较慢或被墙。我们提供以下解决方案：

### 方案一：使用国内CDN加速（推荐）
- **jsDelivr**: `https://cdn.jsdelivr.net/gh/{username}/daily-social-jokes@latest/site/...`
- **gitee.io**: 将项目同步到 Gitee Pages
- **Vercel**: 全球CDN加速（国内访问较快）
- **Cloudflare Pages**: 全球加速

### 方案二：配置自定义域名
接入 ICP 备案的域名，通过国内云服务商（阿里云/腾讯云）的 CDN 加速。

### 方案三：使用镜像站
在 README 中同时提供多个访问链接，方便不同地区的用户访问。

## 🔧 API 密钥配置

本项目主要平台（X/抖音/快手/小红书）**免登录、免APIKey**即可获取真实热门数据。可选配置（GitHub Secrets）：

- `YOUTUBE_API_KEY`: YouTube Data API 密钥（可选，配置后获取真实热门视频，否则为模拟数据）
- `XHS_COOKIE`: 小红书 cookie（可选，兜底解决小红书反爬返回空壳的问题）
- `PROXY_URL`: 代理地址（可选，traversal 海外runner访问国内接口风控时使用）

> **重要**：抖音/快手/小红书接口在国内/部分环境下可正常访问（本地实测均返回真实数据）。
> GitHub Actions 海外 runner 访问这些国内接口可能被风控拦截，可配置 `PROXY_URL` 或在
> 国内机器定时运行爬虫后 push 结果。

## 📝 自定义

- **修改平台**：编辑 `config.json` 中的 `platforms` 字段
- **修改笑话风格**：编辑 `scripts/generators/joke_generator.py`
- **修改主题**：编辑 `site/css/style.css`

## 📄 许可

MIT License