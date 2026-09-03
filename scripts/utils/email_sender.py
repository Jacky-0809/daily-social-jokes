#!/usr/bin/env python3
"""
邮件发送器
把 PDF 报告作为附件发送到指定邮箱（默认 j68251389@gmail.com）
使用 Gmail SMTP，需环境变量/Secrets: GMAIL_USER, GMAIL_APP_PASSWORD
"""

import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from email.header import Header


def send_report_email(pdf_path, date_str, to_addr="j68251389@gmail.com"):
    """发送带 PDF 附件的报告邮件"""
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").strip()

    if not gmail_user or not gmail_pass:
        print("⚠️  未配置 GMAIL_USER / GMAIL_APP_PASSWORD，跳过发送邮件")
        return False

    subject = f"📊 社交平台热点与笑话周报 {date_str}"
    body = (
        f"你好，\n\n"
        f"这是 {date_str} 的社交平台热点与笑话报告，详见附件 PDF。\n\n"
        f"内容包括：\n"
        f"· 今日热点汇总榜\n"
        f"· 每个平台（X/YouTube/小红书/抖音/快手）的笑话/搞笑 Top10\n\n"
        f"数据来源：各平台公开数据，仅供娱乐参考，已自动排除伤亡/时政类敏感新闻。\n\n"
        f"—— 每日社交平台热门榜 自动发送"
    )

    msg = MIMEMultipart()
    msg["From"] = f"Daily Social Jokes <{gmail_user}>"
    msg["To"] = to_addr
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with open(pdf_path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
    filename = f"social_report_{date_str}.pdf"
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=60) as server:
            server.login(gmail_user, gmail_pass)
            server.sendmail(gmail_user, [to_addr], msg.as_string())
        print(f"✅ 邮件已发送到 {to_addr}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


if __name__ == "__main__":
    import sys
    pdf = sys.argv[1] if len(sys.argv) > 1 else "report.pdf"
    date = sys.argv[2] if len(sys.argv) > 2 else "2026-09-03"
    to = sys.argv[3] if len(sys.argv) > 3 else "j68251389@gmail.com"
    send_report_email(pdf, date, to)
