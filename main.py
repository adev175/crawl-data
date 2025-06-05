from services.fetcher import fetch_ai_news
from services.formatter import format_ai_news
from services.telegram_bot import send_to_telegram
from utils.ai_summarizer import summarize_news_with_gemini
from config import USER_TAG

def main():
    print("Starting AI news bot...")

    news_items = fetch_ai_news(8)

    # Nếu lấy được data (danh sách có dữ liệu)
    if news_items:
        # Gửi danh sách tin tức AI mới nhất
        message = format_ai_news(news_items)
        send_to_telegram(message, parse_mode="Markdown", disable_web_page_preview=True)
        # # Gọi Gemini tổng hợp
        # gemini_api_key = os.getenv("GEMINI_API_KEY")
        # ai_summary = summarize_news_with_gemini(news_items, api_key=gemini_api_key)

        # Nếu muốn tag ai đó để chú ý tin nóng
        tag_str = f" {USER_TAG}" if USER_TAG else ""
        send_to_telegram(f"🔔 Update tin AI mới nha{tag_str} 🤖", parse_mode=None)
    else:
        # Thông báo lỗi khi không lấy được tin
        print("Không lấy được tin tức AI mới.")
        send_to_telegram("Bot AI News bị lỗi: Không lấy được tin tức AI mới.", parse_mode=None)

    print("AI news bot finished.")

if __name__ == "__main__":
    main()