import requests
from config import TELEGRAM_URL, CHAT_ID, TIMEOUT

def send_to_telegram(message, parse_mode="Markdown", disable_web_page_preview=True):
    """
    Gửi tin nhắn đến Telegram bằng Bot.
    - parse_mode: "Markdown", "MarkdownV2", "HTML", hoặc None
    - disable_web_page_preview: Ẩn/hiện preview link (nên dùng True với tin tức)
    """
    print("Sending message to Telegram...")
    try:
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'disable_web_page_preview': disable_web_page_preview
        }
        if parse_mode:
            payload['parse_mode'] = parse_mode

        response = requests.post(
            TELEGRAM_URL,
            data=payload,
            timeout=TIMEOUT
        )
        if response.status_code != 200:
            print(f"Error sending message: {response.status_code}, {response.text}")
        else:
            print("Message sent successfully.")
    except requests.RequestException as e:
        print(f"Error sending message to Telegram: {e}")