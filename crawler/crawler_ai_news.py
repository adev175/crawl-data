# crawler_ai_news.py
from services.fetcher import fetch_ai_news
from services.formatter import format_ai_news
from services.telegram_bot import send_to_telegram
from config import USER_TAG

def run_ai_bot():
    print("Starting AI news bot...")
    news_items = fetch_ai_news(8)
    if news_items:
        message = format_ai_news(news_items)
        send_to_telegram(message, parse_mode="Markdown", disable_web_page_preview=True)
        tag_str = f" {USER_TAG}" if USER_TAG else ""
        send_to_telegram(f"🔔 Update tin AI mới nha{tag_str} 🤖", parse_mode=None)
    else:
        print("Không lấy được tin tức AI mới.")
        send_to_telegram("Bot AI News bị lỗi: Không lấy được tin tức AI mới.", parse_mode=None)
    print("AI news bot finished.")

if __name__ == "__main__":
    run_ai_bot()
