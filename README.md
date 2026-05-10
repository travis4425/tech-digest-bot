# 📬 Tech Digest Bot

Tự động gửi bản tin công nghệ & AI **2 lần/ngày** (7h sáng + 7h tối giờ Singapore) vào Gmail của bạn.

**Nguồn tin:** TechCrunch, The Verge, Hacker News, MIT Tech Review, VentureBeat, Anthropic Blog, Reddit (r/MachineLearning, r/LocalLLaMA, r/singularity, r/programming), Dev.to, InfoQ

**Powered by:** Claude AI (Anthropic) để phân tích và tóm tắt thông minh.

---

## ⚡ Setup — 4 bước, ~10 phút

### Bước 1 — Fork repo này lên GitHub

Nhấn nút **Fork** góc trên phải của repo.

---

### Bước 2 — Lấy Gmail App Password

> ⚠️ **QUAN TRỌNG:** Dùng App Password, KHÔNG phải mật khẩu Gmail thông thường.

1. Vào [myaccount.google.com/security](https://myaccount.google.com/security)
2. Bật **2-Step Verification** (nếu chưa bật)
3. Tìm **"App passwords"** (hoặc vào [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords))
4. Tạo app password mới → chọn **"Mail"** → **"Other"** → đặt tên `Tech Digest Bot`
5. Copy dãy 16 ký tự được tạo ra (ví dụ: `abcd efgh ijkl mnop`)

---

### Bước 3 — Lấy Anthropic API Key

1. Vào [console.anthropic.com](https://console.anthropic.com)
2. Vào **API Keys** → **Create Key**
3. Copy key (bắt đầu bằng `sk-ant-...`)

> 💰 Chi phí ước tính: ~$0.02–0.05 USD/lần chạy, tức khoảng **$1–3/tháng**.

---

### Bước 4 — Cài đặt Secrets trên GitHub

Vào repo đã fork → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Tạo 4 secrets sau:

| Secret Name | Giá trị |
|---|---|
| `GMAIL_ADDRESS` | email của bạn (vd: `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | App Password 16 ký tự ở Bước 2 |
| `RECIPIENT_EMAIL` | email nhận báo cáo (có thể giống Gmail Address) |
| `ANTHROPIC_API_KEY` | API key từ Bước 3 |

---

## ✅ Test ngay không cần chờ

1. Vào tab **Actions** trên GitHub
2. Chọn workflow **"Tech Digest — Daily Report"**
3. Nhấn **"Run workflow"** → **"Run workflow"**
4. Chờ ~2 phút → kiểm tra Gmail!

---

## 📧 Format email bạn sẽ nhận

```
Subject: [Tech Digest ☀️ Sáng] Headline nổi bật nhất — 10/05/2026

┌─────────────────────────────────────┐
│  📋 Tóm Tắt Nhanh                  │
│  Executive summary 2-3 câu          │
├─────────────────────────────────────┤
│  ⭐ Top Picks — Không Thể Bỏ Qua   │
│  #1 Bài quan trọng nhất             │
│  #2 Bài thứ 2                       │
│  #3 Bài thứ 3                       │
├─────────────────────────────────────┤
│  🤖 Claude & Anthropic              │
│  🧠 AI & Machine Learning           │
│  💻 Software Engineering            │
│  🔥 Hot on Reddit                   │
│  📱 Big Tech & Industry             │
├─────────────────────────────────────┤
│  💡 Insight Của Ngày                │
└─────────────────────────────────────┘
```

---

## 🛠️ Tuỳ chỉnh

**Thêm nguồn RSS:** Mở `main.py`, thêm vào list `RSS_FEEDS`:
```python
("Tên nguồn", "https://link-rss-cua-nguon.com/feed"),
```

**Đổi giờ nhận:** Mở `.github/workflows/daily_report.yml`, sửa cron:
```yaml
# Format: 'phút giờ * * *' (giờ UTC)
# Singapore UTC+8, nên trừ 8 giờ
- cron: '0 23 * * *'   # 7h sáng SG
- cron: '0 11 * * *'   # 7h tối SG
```

**Đổi ngôn ngữ báo cáo:** Sửa prompt trong hàm `analyse_with_claude()` ở `main.py`.

---

## ❓ Troubleshooting

**Email không đến:**
- Kiểm tra thư mục Spam
- Verify Gmail App Password đúng chưa (không phải password thông thường)

**Workflow bị fail:**
- Vào Actions → click vào run bị lỗi → đọc log
- 99% là do sai secret name hoặc secret value

**Không thấy tab Actions:**
- Vào Settings → Actions → General → chọn "Allow all actions"

---

## 📁 Cấu trúc project

```
tech-digest/
├── main.py                          # Script chính
├── requirements.txt                 # Python dependencies
├── .github/
│   └── workflows/
│       └── daily_report.yml        # GitHub Actions config
└── README.md                        # File này
```
