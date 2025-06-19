# services/event_checker_service.py
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram
from datetime import datetime, timedelta, timezone
from utils.day_converter import convert_day_to_vietnamese


class EventCheckerService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="event_checker",
            description="Latest events from イイベントチェッカー",
            keywords=["event", "events", "イベント", "event checker", "sự kiện", "su kien"],
            emoji="🎪",
            category="events",
            requires_env=["BOT_TOKEN", "CHAT_ID"]
        )

    def execute(self) -> bool:
        try:
            from crawler.crawler_event_checker import fetch_events, format_events

            print("Starting Event Checker service...")
            events = fetch_events(max_events=8)

            if events:
                message = format_events(events)
                send_to_telegram(message, parse_mode="Markdown", disable_web_page_preview=True)

                # Send notification with user tag
                import os
                user_tag = os.getenv('USER_TAG', '')
                tag_str = f" {user_tag}" if user_tag else ""
                send_to_telegram(f"🎪 Cập nhật sự kiện mới nha{tag_str} ✨", parse_mode=None)

                print("✅ Event Checker service completed successfully")
                return True
            else:
                print("❌ No events found")
                send_to_telegram("🎪 Không tìm thấy sự kiện mới từ Event Checker", parse_mode=None)
                return False

        except Exception as e:
            print(f"Event Checker service error: {e}")
            send_to_telegram(f"❌ Lỗi Event Checker bot: {str(e)[:100]}...", parse_mode=None)
            return False