# telegram_chatbot.py
import os
import time
import threading
from datetime import datetime
import requests
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
USER_TAG = os.getenv('USER_TAG', '')


class TelegramChatBot:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.last_update_id = 0
        self.running = False

        # Bot commands and keywords
        self.commands = {
            # Bus related
            'bus': ['bus', 'xe', 'xe buýt', 'bus time', 'bus price', 'giá xe'],

            # Gold related
            'gold': ['gold', 'vàng', 'giá vàng', 'vang', 'gia vang'],

            # AI News related
            'ai': ['ai', 'ai news', 'tin ai', 'news', 'tin tức', 'tech news'],

            # Help and status
            'help': ['help', 'trợ giúp', 'commands', 'menu', '/start', '/help'],
            'status': ['status', 'tình trạng', 'ping', 'alive'],

            # All bots
            'all': ['all', 'tất cả', 'all bots', 'run all', 'chạy tất cả']
        }

    def send_message(self, text, parse_mode=None):
        """Send message to Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text
            }
            if parse_mode:
                data['parse_mode'] = parse_mode

            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def get_updates(self):
        """Get updates from Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                'offset': self.last_update_id + 1,
                'timeout': 10
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting updates: {e}")
            return None

    def classify_message(self, text):
        """Classify user message to determine which bot to run"""
        text_lower = text.lower().strip()

        # Check each command category
        for category, keywords in self.commands.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category

        # Default response for unrecognized messages
        return 'help'

    def run_bus_bot(self):
        """Run bus price bot"""
        try:
            self.send_message("🚌 Đang kiểm tra giá xe bus... Vui lòng đợi!")

            from crawler.crawler_bus_price_complete import BusPriceTracker
            tracker = BusPriceTracker()
            tracker.run()

            print("✅ Bus bot completed")
        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy bus bot: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def run_gold_bot(self):
        """Run gold price bot"""
        try:
            self.send_message("🪙 Đang kiểm tra giá vàng... Vui lòng đợi!")

            # Try enhanced version first for better reliability
            try:
                from crawler.crawler_gold_enhanced import main as enhanced_gold_main
                enhanced_gold_main()
            except ImportError:
                # Fallback to standard version
                from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram
                buy_trend, data = fetch_gold_prices()
                if data:
                    send_to_telegram(format_as_code_block(data))
                    if buy_trend == 'increase':
                        send_to_telegram(f"Có nên mua vàng không má {USER_TAG} 🤔🤔🤔", parse_mode=None)
                    elif buy_trend == 'decrease':
                        send_to_telegram(f"✅ Mua vàng đi má {USER_TAG} 🧀🧀🧀", parse_mode=None)
                else:
                    self.send_message("❌ Không thể lấy dữ liệu giá vàng")

            print("✅ Gold bot completed")
        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy gold bot: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def run_ai_bot(self):
        """Run AI news bot"""
        try:
            self.send_message("🤖 Đang lấy tin tức AI mới nhất... Vui lòng đợi!")

            from crawler.crawl_ai_news import run_ai_bot
            run_ai_bot()

            print("✅ AI news bot completed")
        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy AI news bot: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def run_all_bots(self):
        """Run all bots sequentially"""
        try:
            self.send_message("🚀 Chạy tất cả bots... Có thể mất vài phút!")

            # Run each bot
            self.run_ai_bot()
            time.sleep(2)
            self.run_gold_bot()
            time.sleep(2)
            self.run_bus_bot()

            self.send_message("✅ Đã chạy xong tất cả bots!")
            print("✅ All bots completed")
        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy all bots: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def show_help(self):
        """Show help message with available commands"""
        help_text = f"""🤖 Chatbot Commands:

🚌 **Bus Commands:**
• "bus" / "xe" / "bus time" / "giá xe"
→ Kiểm tra giá xe bus Nagaoka → Shinjuku

🪙 **Gold Commands:**  
• "gold" / "vàng" / "giá vàng"
→ Kiểm tra giá vàng hôm nay

🤖 **AI News Commands:**
• "ai" / "news" / "tin ai" / "tin tức"  
→ Tin tức AI mới nhất từ CNBC

🚀 **Other Commands:**
• "all" / "tất cả" → Chạy tất cả bots
• "status" / "ping" → Kiểm tra bot có hoạt động
• "help" / "trợ giúp" → Hiển thị menu này

💬 **Cách sử dụng:**
Chỉ cần nhắn một trong các từ khóa trên!

VD: "bus time" → Bot sẽ tự động check giá xe
"""
        self.send_message(help_text)

    def show_status(self):
        """Show bot status"""
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        status_text = f"""🟢 Bot đang hoạt động!

⏰ Thời gian: {current_time}
🤖 Chatbot: Online
📱 Telegram: Connected
{USER_TAG} Status: Active

Nhắn "help" để xem commands!"""

        self.send_message(status_text)

    def handle_message(self, message):
        """Handle incoming message"""
        try:
            text = message.get('text', '')
            user = message.get('from', {})
            chat = message.get('chat', {})

            username = user.get('username', user.get('first_name', 'Unknown'))

            print(f"📨 Message from {username}: {text}")

            # Classify and respond
            command = self.classify_message(text)

            if command == 'bus':
                # Run in background thread to avoid blocking
                threading.Thread(target=self.run_bus_bot, daemon=True).start()

            elif command == 'gold':
                threading.Thread(target=self.run_gold_bot, daemon=True).start()

            elif command == 'ai':
                threading.Thread(target=self.run_ai_bot, daemon=True).start()

            elif command == 'all':
                threading.Thread(target=self.run_all_bots, daemon=True).start()

            elif command == 'status':
                self.show_status()

            elif command == 'help':
                self.show_help()

            else:
                # Unrecognized command
                self.send_message(f"🤔 Không hiểu '{text}'\n\nNhắn 'help' để xem các commands có sẵn!")

        except Exception as e:
            print(f"Error handling message: {e}")
            self.send_message("❌ Có lỗi xảy ra khi xử lý tin nhắn")

    def start_polling(self):
        """Start bot polling loop"""
        print("🤖 Starting Telegram chatbot...")
        print(f"Bot token: {self.bot_token[:10]}..." if self.bot_token else "❌ No bot token")
        print(f"Chat ID: {self.chat_id}")

        if not self.bot_token or not self.chat_id:
            print("❌ Missing BOT_TOKEN or CHAT_ID")
            return

        # Send startup message
        self.send_message(f"🤖 Chatbot started! {USER_TAG}\n\nNhắn 'help' để xem commands.")

        self.running = True
        error_count = 0
        max_errors = 5

        while self.running:
            try:
                # Get updates
                updates_data = self.get_updates()

                if updates_data and updates_data.get('ok'):
                    updates = updates_data.get('result', [])

                    for update in updates:
                        self.last_update_id = update['update_id']

                        if 'message' in update:
                            self.handle_message(update['message'])

                # Reset error count on success
                error_count = 0
                time.sleep(1)  # Small delay to avoid rate limiting

            except KeyboardInterrupt:
                print("\n🛑 Stopping chatbot...")
                self.running = False
                self.send_message("🛑 Chatbot stopped")

            except Exception as e:
                error_count += 1
                print(f"❌ Error in polling loop: {e} (attempt {error_count}/{max_errors})")

                if error_count >= max_errors:
                    print("💀 Too many errors, stopping bot")
                    self.send_message("❌ Bot gặp lỗi quá nhiều, tạm dừng hoạt động")
                    break

                time.sleep(5)  # Wait before retry

    def stop(self):
        """Stop the bot"""
        self.running = False


def main():
    """Main function"""
    bot = TelegramChatBot()

    try:
        bot.start_polling()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        bot.stop()


if __name__ == "__main__":
    main()