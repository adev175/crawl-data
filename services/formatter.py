from datetime import datetime, timedelta, timezone
from utils.day_converter import convert_day_to_vietnamese

def format_ai_news(news_items, max_items=5):
    """
    Định dạng danh sách tin tức AI theo dạng markdown link + mô tả ngắn gọn.
    """
    print("Formatting AI news for Telegram...")
    now = datetime.now(timezone.utc) + timedelta(hours=7)
    current_time = now.strftime("%H:%M:%S")
    current_day = convert_day_to_vietnamese(now.strftime("%A"))
    current_date = now.strftime("%d/%m/%Y")

    message_lines = [
        f"{current_time} {current_day} {current_date}: Tin tức AI mới nhất từ CNBC 🤖",
        ""
    ]

    for idx, news in enumerate(news_items[:max_items], 1):
        # Markdown link: [title](url)
        title_line = f"{idx}. [{news['title']}]({news['link']})"
        message_lines.append(title_line)
        # Thời gian đăng (nếu có)
        if news.get('time'):
            message_lines.append(f"    🕒 {news['time']}")
        # Mô tả ngắn (nếu có)
        if news.get('summary'):
            message_lines.append(f"    📝 {news['summary']}")
        message_lines.append("")  # Dòng trống giữa các tin

    print("AI news formatted successfully.")
    return "\n".join(message_lines).strip()