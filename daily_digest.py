import os
import json
import urllib.request
import urllib.parse
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header

# 获取最近7天创建、受关注的 GitHub 项目
since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
query = urllib.parse.urlencode({
    "q": f"created:>={since} stars:>30",
    "sort": "stars",
    "order": "desc",
    "per_page": 10
})

url = "https://api.github.com/search/repositories?" + query
request = urllib.request.Request(
    url,
    headers={"Accept": "application/vnd.github+json",
             "User-Agent": "GitHub-Daily-Digest"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    data = json.loads(response.read().decode("utf-8"))

def translate_to_chinese(text):
    """将项目简介翻译成简体中文；翻译服务不可用时保留原文。"""
    if not text:
        return "暂无简介"
    try:
        params = urllib.parse.urlencode({
            "client": "gtx",
            "sl": "auto",
            "tl": "zh-CN",
            "dt": "t",
            "q": text
        })
        translate_url = "https://translate.googleapis.com/translate_a/single?" + params
        translate_request = urllib.request.Request(
            translate_url,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(translate_request, timeout=15) as response:
            translated_data = json.loads(response.read().decode("utf-8"))
        translated = "".join(part[0] for part in translated_data[0] if part[0])
        return translated or text
    except Exception:
        return text


today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
lines = [
    f"GitHub 热门项目日报 - {today}",
    "",
    "以下为最近7天创建、按 Star 数排序的项目精选：",
    ""
]

for i, repo in enumerate(data.get("items", []), 1):
    lines.extend([
        f"{i}. {repo['full_name']}",
        f"项目简介（中文）：{translate_to_chinese(repo.get('description'))}",
        f"Stars：{repo['stargazers_count']}",
        f"语言：{repo.get('language') or '未注明'}",
        f"地址：{repo['html_url']}",
        ""
    ])

body = "\n".join(lines)

# 仅使用 Gmail SMTP，日报只发送到 Gmail
sender = os.environ["GMAIL_EMAIL"]
password = os.environ["GMAIL_APP_PASSWORD"]
receiver = "luojiawan666894@gmail.com"

message = MIMEText(body, "plain", "utf-8")
message["Subject"] = Header(f"GitHub 每日热门项目日报 {today}", "utf-8")
message["From"] = sender
message["To"] = receiver

with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
    server.login(sender, password)
    server.sendmail(sender, [receiver], message.as_string())

print("GitHub 每日日报已提交发送至 Gmail！")
