# telegram_chatbot.py - Webhook Version
import os
import time
import threading
from datetime import datetime
import requests
import json
from dotenv import load_dotenv
from flask import Flask, request
import hashlib
import hmac

# Load environment
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
USER_TAG = os.getenv('USER_TAG', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # https://yourserver.com/telegram-webhook
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-secret-key')  # Để verify webhook

# Flask app for webhook
app = Flask(__name__)


class TelegramChatBot:
    def __init__(self):
        self.bot_token = BOT_TOKEN
        self.chat_id = CHAT_ID
        self.webhook_url = WEBHOOK_URL
        self.webhook_secret = WEBHOOK_SECRET

        # Bot commands and keywords (giữ nguyên)
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

    def set_webhook(self):
        """Đăng ký webhook với Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            data = {
                'url': self.webhook_url,
                'allowed_updates': ['message'],
                'drop_pending_updates': True  # Xóa các update cũ
            }

            # Thêm secret token để verify (tùy chọn)
            if self.webhook_secret:
                data['secret_token'] = self.webhook_secret

            response = requests.post(url, data=data, timeout=10)
            result = response.json()

            if result.get('ok'):
                print(f"✅ Webhook set successfully: {self.webhook_url}")
                return True
            else:
                print(f"❌ Failed to set webhook: {result}")
                return False

        except Exception as e:
            print(f"❌ Error setting webhook: {e}")
            return False

    def delete_webhook(self):
        """Xóa webhook (chuyển về polling)"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
            response = requests.post(url, timeout=10)
            result = response.json()

            if result.get('ok'):
                print("✅ Webhook deleted successfully")
                return True
            else:
                print(f"❌ Failed to delete webhook: {result}")
                return False

        except Exception as e:
            print(f"❌ Error deleting webhook: {e}")
            return False

    def get_webhook_info(self):
        """Kiểm tra thông tin webhook hiện tại"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
            response = requests.get(url, timeout=10)
            result = response.json()

            if result.get('ok'):
                info = result['result']
                print(f"🔍 Webhook Info:")
                print(f"   URL: {info.get('url', 'None')}")
                print(f"   Pending updates: {info.get('pending_update_count', 0)}")
                print(f"   Last error: {info.get('last_error_message', 'None')}")
                return info
            return None

        except Exception as e:
            print(f"❌ Error getting webhook info: {e}")
            return None

    def verify_webhook_signature(self, request):
        """Verify webhook đến từ Telegram (bảo mật)"""
        if not self.webhook_secret:
            return True  # Nếu không set secret thì bỏ qua verify

        try:
            # Lấy signature từ header
            telegram_signature = request.headers.get('X-Telegram-Bot-Api-Secret-Token')

            if not telegram_signature:
                print("⚠️ Missing webhook signature")
                return False

            # So sánh với secret đã set
            return telegram_signature == self.webhook_secret

        except Exception as e:
            print(f"❌ Error verifying signature: {e}")
            return False

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

🎣 **Mode: Webhook (Realtime)**
"""
        self.send_message(help_text)

    def show_status(self):
        """Show bot status"""
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

        # Kiểm tra webhook info
        webhook_info = self.get_webhook_info()
        webhook_status = "✅ Active" if webhook_info and webhook_info.get('url') else "❌ Not set"

        status_text = f"""🟢 Bot đang hoạt động!

⏰ Thời gian: {current_time}
🤖 Chatbot: Online  
📱 Telegram: Connected
🎣 Webhook: {webhook_status}
{USER_TAG} Status: Active

Nhắn "help" để xem commands!"""

        self.send_message(status_text)

    def handle_message(self, message):
        """Handle incoming message from webhook"""
        try:
            text = message.get('text', '')
            user = message.get('from', {})
            chat = message.get('chat', {})

            username = user.get('username', user.get('first_name', 'Unknown'))

            print(f"🎣 Webhook message from {username}: {text}")

            # Classify and respond
            command = self.classify_message(text)

            if command == 'bus':
                # Run in background thread to avoid blocking webhook response
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
            print(f"Error handling webhook message: {e}")
            self.send_message("❌ Có lỗi xảy ra khi xử lý tin nhắn")


# Global bot instance
bot_instance = TelegramChatBot()


# Flask routes
@app.route('/')
def home():
    """Health check endpoint"""
    return {
        'status': 'Bot is running',
        'mode': 'webhook',
        'timestamp': datetime.now().isoformat()
    }


@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Nhận webhook từ Telegram"""
    try:
        # Verify request đến từ Telegram
        if not bot_instance.verify_webhook_signature(request):
            print("⚠️ Invalid webhook signature")
            return 'Unauthorized', 401

        # Parse webhook data
        update = request.get_json()

        if not update:
            print("⚠️ Empty webhook data")
            return 'Bad Request', 400

        print(f"🎣 Webhook received: {update.get('update_id')}")

        # Handle message
        if 'message' in update:
            bot_instance.handle_message(update['message'])

        # Telegram expects quick response
        return 'OK', 200

    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return 'Internal Server Error', 500


@app.route('/webhook/setup', methods=['POST'])
def setup_webhook():
    """Endpoint để setup webhook"""
    try:
        if bot_instance.set_webhook():
            return {'status': 'success', 'message': 'Webhook set successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to set webhook'}, 500
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/webhook/delete', methods=['POST'])
def delete_webhook():
    """Endpoint để xóa webhook"""
    try:
        if bot_instance.delete_webhook():
            return {'status': 'success', 'message': 'Webhook deleted successfully'}
        else:
            return {'status': 'error', 'message': 'Failed to delete webhook'}, 500
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/webhook/info', methods=['GET'])
def webhook_info():
    """Endpoint để kiểm tra webhook info"""
    try:
        info = bot_instance.get_webhook_info()
        return {'status': 'success', 'webhook_info': info}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


@app.route('/send-test', methods=['POST'])
def send_test_message():
    """Endpoint để test gửi tin nhắn"""
    try:
        data = request.get_json()
        message = data.get('message', 'Test message from webhook bot!')

        if bot_instance.send_message(message):
            return {'status': 'success', 'message': 'Test message sent'}
        else:
            return {'status': 'error', 'message': 'Failed to send message'}, 500
    except Exception as e:
        return {'status': 'error', 'message': str(e)}, 500


def start_webhook_server():
    """Start webhook server"""
    print("🎣 Starting Telegram Webhook Bot...")
    print(f"Bot token: {BOT_TOKEN[:10]}..." if BOT_TOKEN else "❌ No bot token")
    print(f"Chat ID: {CHAT_ID}")
    print(f"Webhook URL: {WEBHOOK_URL}")

    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Missing BOT_TOKEN or CHAT_ID")
        return

    if not WEBHOOK_URL:
        print("❌ Missing WEBHOOK_URL - required for webhook mode")
        print("💡 Set WEBHOOK_URL in .env file: https://yourserver.com/telegram-webhook")
        return

    # Setup webhook
    if bot_instance.set_webhook():
        # Send startup message
        bot_instance.send_message(
            f"🎣 Webhook Bot started! {USER_TAG}\n\nMode: Realtime Webhook\nNhắn 'help' để xem commands.")

        # Start Flask server
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print("❌ Failed to setup webhook")


def start_polling_fallback():
    """Fallback to polling mode if webhook fails"""
    print("🔄 Falling back to polling mode...")

    # Delete any existing webhook first
    bot_instance.delete_webhook()
    time.sleep(2)

    # Start polling (old method)
    bot_instance.running = True
    error_count = 0
    max_errors = 5

    while bot_instance.running:
        try:
            # Get updates (polling method)
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {
                'offset': bot_instance.last_update_id + 1,
                'timeout': 10
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                updates_data = response.json()

                if updates_data.get('ok'):
                    updates = updates_data.get('result', [])

                    for update in updates:
                        bot_instance.last_update_id = update['update_id']

                        if 'message' in update:
                            bot_instance.handle_message(update['message'])

            # Reset error count on success
            error_count = 0
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping chatbot...")
            bot_instance.running = False
            bot_instance.send_message("🛑 Chatbot stopped")

        except Exception as e:
            error_count += 1
            print(f"❌ Error in polling: {e} (attempt {error_count}/{max_errors})")

            if error_count >= max_errors:
                print("💀 Too many errors, stopping bot")
                break

            time.sleep(5)


def main():
    """Main function - Auto choose webhook or polling"""
    mode = os.getenv('BOT_MODE', 'auto').lower()

    if mode == 'polling':
        print("🔄 Force polling mode")
        start_polling_fallback()
    elif mode == 'webhook' or (mode == 'auto' and WEBHOOK_URL):
        print("🎣 Using webhook mode")
        try:
            start_webhook_server()
        except Exception as e:
            print(f"❌ Webhook failed: {e}")
            print("🔄 Falling back to polling...")
            start_polling_fallback()
    else:
        print("🔄 Using polling mode (no webhook URL)")
        start_polling_fallback()


if __name__ == "__main__":
    main()