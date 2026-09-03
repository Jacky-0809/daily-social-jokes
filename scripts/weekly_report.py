#!/usr/bin/env python3
"""
周报处理：生成 PDF 并发送邮件
被 GitHub Actions 每周五定时触发（run.py 抓取后调用）
用法: python scripts/weekly_report.py [date]
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from generators.pdf_generator import generate_pdf            # noqa: E402
from utils.email_sender import send_report_email             # noqa: E402


def latest_data_file():
    data_dir = ROOT / "data"
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError("未找到任何数据文件")
    return files[-1]


def main():
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if date_arg:
        data_file = ROOT / "data" / f"{date_arg}.json"
        if not data_file.exists():
            raise FileNotFoundError(f"数据文件不存在: {data_file}")
    else:
        data_file = latest_data_file()

    with open(data_file, encoding="utf-8") as f:
        data = json.load(f)

    date_str = data["date"]

    # 1. 生成 PDF 到 output/ 目录
    pdf_dir = ROOT / "output"
    pdf_dir.mkdir(exist_ok=True)
    pdf_path = pdf_dir / f"social_report_{date_str}.pdf"
    generate_pdf(data, str(pdf_path))
    print(f"PDF 生成成功: {pdf_path}")

    # 2. 发送到指定邮箱
    to_addr = os.environ.get("REPORT_EMAIL_TO", "j68251389@gmail.com")
    ok = send_report_email(str(pdf_path), date_str, to_addr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
