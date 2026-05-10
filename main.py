import os
import json
import smtplib
import feedparser
import requests
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import google.generativeai as genai

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SENDER_EMAIL    = os.environ["GMAIL_ADDRESS"]
SENDER_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", SENDER_EMAIL)
ANTHROPIC_KEY   = os.environ["ANTHROPIC_API_KEY"]

RSS_FEEDS = [
    # Tech / AI general
    ("TechCrunch AI",        "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("The Verge Tech",       "https://www.theverge.com/rss/index.xml"),
    ("Hacker News Top",      "https://hnrss.org/frontpage?points=100"),
    ("MIT Tech Review AI",   "https://www.technologyreview.com/feed/"),
    ("VentureBeat AI",       "https://venturebeat.com/category/ai/feed/"),
    # Anthropic / Claude
    ("Anthropic Blog",       "https://www.anthropic.com/rss.xml"),
    # Reddit
    ("r/MachineLearning",    "https://www.reddit.com/r/MachineLearning/.rss"),
    ("r/LocalLLaMA",         "https://www.reddit.com/r/LocalLLaMA/.rss"),
    ("r/singularity",        "https://www.reddit.com/r/singularity/.rss"),
    ("r/programming",        "https://www.reddit.com/r/programming/.rss"),
    # Software Engineering
    ("Dev.to",               "https://dev.to/feed"),
    ("InfoQ",                "https://feed.infoq.com/"),
]

MAX_ITEMS_PER_FEED = 5
MAX_ITEMS_TOTAL    = 40
# ──────────────────────────────────────────────────────────────────────────────


def fetch_articles() -> list[dict]:
    """Fetch latest articles from all RSS feeds."""
    articles = []
    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:MAX_ITEMS_PER_FEED]:
                summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
                # Strip HTML tags simply
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:500]
                articles.append({
                    "source": source_name,
                    "title":  entry.get("title", "No title"),
                    "link":   entry.get("link", ""),
                    "summary": summary.strip(),
                    "published": entry.get("published", ""),
                })
        except Exception as e:
            print(f"[WARN] Failed to fetch {source_name}: {e}")

    # Deduplicate by title and limit total
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:MAX_ITEMS_TOTAL]


def analyse_with_claude(articles: list[dict], session: str) -> dict:
    """Send articles to Claude for analysis and structured digest."""
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

    articles_text = "\n\n".join([
        f"[{i+1}] SOURCE: {a['source']}\nTITLE: {a['title']}\nURL: {a['link']}\nSUMMARY: {a['summary']}"
        for i, a in enumerate(articles)
    ])

    session_label = "SÁNG" if session == "morning" else "TỐI"
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    prompt = f"""Bạn là một AI analyst chuyên về công nghệ phần mềm và AI. Hôm nay là {now_str}, buổi {session_label}.

Dưới đây là các bài báo mới nhất từ nhiều nguồn khác nhau. Hãy phân tích và tạo một bản tin tổng hợp CHẤT LƯỢNG CAO bằng tiếng Việt.

=== BÀI BÁO RAW ===
{articles_text}

=== YÊU CẦU OUTPUT ===
Trả về JSON THUẦN (không có markdown, không có backtick) với cấu trúc:
{{
  "headline": "Tiêu đề nổi bật nhất của ngày (1 câu súc tích)",
  "executive_summary": "Tóm tắt tổng quan 2-3 câu về bức tranh công nghệ hôm nay",
  "sections": [
    {{
      "title": "🤖 Claude & Anthropic",
      "items": [
        {{
          "title": "Tiêu đề bài viết",
          "insight": "Phân tích 2-3 câu: chuyện gì xảy ra, tại sao quan trọng, impact gì",
          "url": "link gốc",
          "source": "tên nguồn",
          "importance": "high|medium|low"
        }}
      ]
    }},
    {{
      "title": "🧠 AI & Machine Learning",
      "items": [...]
    }},
    {{
      "title": "💻 Software Engineering",
      "items": [...]
    }},
    {{
      "title": "🔥 Hot on Reddit & Community",
      "items": [...]
    }},
    {{
      "title": "📱 Big Tech & Industry",
      "items": [...]
    }}
  ],
  "top_picks": [
    {{
      "title": "Top 3 bài KHÔNG THỂ BỎ QUA hôm nay",
      "url": "link",
      "why": "lý do 1 câu"
    }}
  ],
  "closing_thought": "Một insight thú vị hoặc câu hỏi để suy ngẫm về xu hướng công nghệ (2-3 câu)"
}}

Lưu ý:
- Ưu tiên tin về Claude/Anthropic lên section đầu tiên
- Chỉ giữ lại bài THỰC SỰ đáng đọc, bỏ qua bài spam/quảng cáo
- Insight phải cụ thể, có giá trị, KHÔNG chung chung
- Nếu không có bài về một section, để items là []
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Remove possible markdown fences
    import re
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"```$", "", raw).strip()

    return json.loads(raw)


def importance_badge(level: str) -> str:
    return {"high": "🔴 Hot", "medium": "🟡 Notable", "low": "🔵 FYI"}.get(level, "🔵 FYI")


def build_html_email(digest: dict, session: str) -> str:
    """Build beautiful HTML email from digest data."""
    session_label = "☀️ Buổi Sáng" if session == "morning" else "🌙 Buổi Tối"
    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    sections_html = ""
    for section in digest.get("sections", []):
        items = section.get("items", [])
        if not items:
            continue
        items_html = ""
        for item in items:
            badge = importance_badge(item.get("importance", "low"))
            items_html += f"""
            <div style="margin-bottom:20px; padding:16px; background:#f8fafc; border-radius:10px; border-left:4px solid #6366f1;">
              <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                <a href="{item['url']}" style="font-size:15px; font-weight:600; color:#1e293b; text-decoration:none; line-height:1.4;">{item['title']}</a>
                <span style="font-size:11px; white-space:nowrap; margin-left:12px; color:#64748b;">{badge}</span>
              </div>
              <p style="margin:0 0 8px 0; font-size:14px; color:#475569; line-height:1.6;">{item['insight']}</p>
              <span style="font-size:12px; color:#94a3b8;">📰 {item.get('source','')}</span>
            </div>"""

        sections_html += f"""
        <div style="margin-bottom:32px;">
          <h2 style="font-size:18px; font-weight:700; color:#1e293b; margin:0 0 16px 0; padding-bottom:8px; border-bottom:2px solid #e2e8f0;">{section['title']}</h2>
          {items_html}
        </div>"""

    top_picks_html = ""
    for i, pick in enumerate(digest.get("top_picks", []), 1):
        top_picks_html += f"""
        <div style="margin-bottom:12px; display:flex; align-items:flex-start; gap:12px;">
          <span style="font-size:20px; font-weight:800; color:#6366f1; min-width:28px;">#{i}</span>
          <div>
            <a href="{pick['url']}" style="font-size:14px; font-weight:600; color:#1e293b; text-decoration:none;">{pick['title']}</a>
            <p style="margin:4px 0 0 0; font-size:13px; color:#64748b;">{pick['why']}</p>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Tech Digest {now_str}</title>
</head>
<body style="margin:0; padding:0; background:#f1f5f9; font-family:'Segoe UI',Arial,sans-serif;">
  <div style="max-width:680px; margin:0 auto; padding:24px 16px;">

    <!-- HEADER -->
    <div style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 50%,#06b6d4 100%); border-radius:16px; padding:32px; margin-bottom:24px; text-align:center;">
      <p style="margin:0 0 4px 0; font-size:13px; color:rgba(255,255,255,0.8); letter-spacing:2px; text-transform:uppercase;">Tech Digest {session_label}</p>
      <h1 style="margin:8px 0; font-size:28px; font-weight:800; color:#fff; line-height:1.3;">{digest.get('headline','Bản tin công nghệ hôm nay')}</h1>
      <p style="margin:12px 0 0 0; font-size:13px; color:rgba(255,255,255,0.75);">{now_str}</p>
    </div>

    <!-- EXECUTIVE SUMMARY -->
    <div style="background:#fff; border-radius:12px; padding:20px 24px; margin-bottom:24px; border:1px solid #e2e8f0;">
      <h2 style="margin:0 0 10px 0; font-size:14px; font-weight:700; color:#6366f1; text-transform:uppercase; letter-spacing:1px;">📋 Tóm Tắt Nhanh</h2>
      <p style="margin:0; font-size:15px; color:#334155; line-height:1.7;">{digest.get('executive_summary','')}</p>
    </div>

    <!-- TOP PICKS -->
    <div style="background:#fefce8; border-radius:12px; padding:20px 24px; margin-bottom:24px; border:1px solid #fde68a;">
      <h2 style="margin:0 0 16px 0; font-size:14px; font-weight:700; color:#92400e; text-transform:uppercase; letter-spacing:1px;">⭐ Top Picks — Không Thể Bỏ Qua</h2>
      {top_picks_html}
    </div>

    <!-- MAIN CONTENT -->
    <div style="background:#fff; border-radius:12px; padding:24px; margin-bottom:24px; border:1px solid #e2e8f0;">
      {sections_html}
    </div>

    <!-- CLOSING THOUGHT -->
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b); border-radius:12px; padding:24px; margin-bottom:24px;">
      <h2 style="margin:0 0 10px 0; font-size:14px; font-weight:700; color:#818cf8; text-transform:uppercase; letter-spacing:1px;">💡 Insight Của Ngày</h2>
      <p style="margin:0; font-size:15px; color:#cbd5e1; line-height:1.7;">{digest.get('closing_thought','')}</p>
    </div>

    <!-- FOOTER -->
    <div style="text-align:center; padding:16px;">
      <p style="margin:0; font-size:12px; color:#94a3b8;">Được tạo tự động bởi Tech Digest Bot • Powered by Claude AI</p>
      <p style="margin:4px 0 0 0; font-size:12px; color:#94a3b8;">Nguồn: TechCrunch, The Verge, HN, MIT Tech Review, Anthropic, Reddit</p>
    </div>

  </div>
</body>
</html>"""
    return html


def send_email(subject: str, html_body: str):
    """Send HTML email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    print(f"[OK] Email sent to {RECIPIENT_EMAIL}")


def main():
    # Determine session based on UTC hour (Singapore = UTC+8)
    sg_hour = (datetime.now(timezone.utc).hour + 8) % 24
    session = "morning" if 5 <= sg_hour < 14 else "evening"

    print(f"[INFO] Running {session} digest (SG time: {sg_hour}h)...")

    articles = fetch_articles()
    print(f"[INFO] Fetched {len(articles)} articles")

    digest = analyse_with_claude(articles, session)
    print("[INFO] Claude analysis complete")

    session_label = "☀️ Sáng" if session == "morning" else "🌙 Tối"
    subject = f"[Tech Digest {session_label}] {digest.get('headline', 'Bản tin công nghệ')} — {datetime.now().strftime('%d/%m/%Y')}"

    html = build_html_email(digest, session)
    send_email(subject, html)


if __name__ == "__main__":
    main()
