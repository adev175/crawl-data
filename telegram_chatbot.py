# telegram_chatbot.py - Updated with Service Registry
import os
import time
import threading
from datetime import datetime
import requests
from dotenv import load_dotenv
from services.service_registry import registry

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
        self.service_registry = registry

        # Built-in system commands
        self.system_commands = {
            'help': ['help', 'trợ giúp', 'commands', 'menu', '/start', '/help'],
            'status': ['status', 'tình trạng', 'ping', 'alive'],
            'all': ['all', 'tất cả', 'all bots', 'run all', 'chạy tất cả'],
            'list': ['list', 'services', 'danh sách', 'available']
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
        """Classify user message to determine action"""
        text_lower = text.lower().strip()

        # Check system commands first
        for command, keywords in self.system_commands.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return ('system', command)

        # Check service registry
        service = self.service_registry.get_service_by_keyword(text)
        if service:
            config = service.get_config()
            return ('service', config.name)

        # Default to help
        return ('system', 'help')

    def execute_service(self, service_name):
        """Execute a service with status updates"""
        try:
            service = self.service_registry.services.get(service_name)
            if not service:
                self.send_message(f"❌ Service '{service_name}' not found")
                return

            config = service.get_config()

            # Send status message
            self.send_message(f"{config.emoji} Đang {config.description.lower()}... Vui lòng đợi!")

            # Execute service
            start_time = datetime.now()
            success = service.execute()
            end_time = datetime.now()

            duration = (end_time - start_time).total_seconds()

            if success:
                self.send_message(f"✅ {config.name} hoàn thành! (Thời gian: {duration:.1f}s)")
            else:
                self.send_message(f"❌ {config.name} thất bại!")

            print(f"{'✅' if success else '❌'} {config.name} completed in {duration:.1f}s")

        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy {service_name}: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def execute_all_services(self):
        """Execute all enabled services"""
        try:
            services = self.service_registry.get_all_services()
            if not services:
                self.send_message("❌ Không có service nào được kích hoạt")
                return

            self.send_message(f"🚀 Chạy tất cả services ({len(services)} services)...")

            completed = 0
            failed = 0

            for i, (name, service) in enumerate(services.items(), 1):
                config = service.get_config()
                self.send_message(f"{i}/{len(services)}: {config.emoji} Đang {config.description.lower()}...")

                success = service.execute()
                if success:
                    completed += 1
                else:
                    failed += 1

                time.sleep(2)  # Delay between services

            summary = f"🎉 Hoàn thành tất cả services!\n\n"
            summary += f"✅ Thành công: {completed}\n"
            summary += f"❌ Thất bại: {failed}\n"
            summary += f"📊 Tổng cộng: {len(services)}"

            self.send_message(summary)
            print(f"All services completed: {completed} success, {failed} failed")

        except Exception as e:
            error_msg = f"❌ Lỗi khi chạy all services: {str(e)}"
            self.send_message(error_msg)
            print(error_msg)

    def show_help(self):
        """Show help message with all available services"""
        help_text = self.service_registry.get_help_text()

        # Add system commands
        help_text += "\n**System Commands:**\n"
        help_text += "• `help` → Show this menu\n"
        help_text += "• `status` → Check bot status\n"
        help_text += "• `all` → Run all services\n"
        help_text += "• `list` → List available services\n"

        self.send_message(help_text, parse_mode="Markdown")

    def show_status(self):
        """Show bot status and available services"""
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        services = self.service_registry.get_all_services()

        status_text = f"""🟢 **Bot Status: Online**

⏰ **Time:** {current_time}
🤖 **Chatbot:** Active
📱 **Telegram:** Connected
🔧 **Services:** {len(services)} available
{USER_TAG} **User:** Active

💬 Send `help` for commands or `list` for services!"""

        self.send_message(status_text, parse_mode="Markdown")

    def list_services(self):
        """List all available services by category"""
        categories = {}

        for service in self.service_registry.get_all_services().values():
            config = service.get_config()
            if config.category not in categories:
                categories[config.category] = []
            categories[config.category].append(config)

        message = "📋 **Available Services:**\n\n"

        for category, configs in categories.items():
            message += f"**{category.title()}** ({len(configs)}):\n"
            for config in configs:
                status = "✅" if config.enabled else "❌"
                message += f"{status} {config.emoji} {config.name}\n"
            message += "\n"

        message += f"💡 Total: {len(self.service_registry.get_all_services())} services\n"
        message += "Type any keyword to trigger a service!"

        self.send_message(message, parse_mode="Markdown")

    def handle_message(self, message):
        """Handle incoming message"""
        try:
            text = message.get('text', '')
            user = message.get('from', {})

            username = user.get('username', user.get('first_name', 'Unknown'))

            print(f"📨 Message from {username}: {text}")

            # Classify message
            action_type, action_value = self.classify_message(text)

            if action_type == 'system':
                if action_value == 'help':
                    self.show_help()
                elif action_value == 'status':
                    self.show_status()
                elif action_value == 'list':
                    self.list_services()
                elif action_value == 'all':
                    threading.Thread(target=self.execute_all_services, daemon=True).start()

            elif action_type == 'service':
                # Execute service in background thread
                threading.Thread(target=self.execute_service, args=(action_value,), daemon=True).start()

            else:
                # Fallback
                suggestions = []
                for service in list(self.service_registry.get_all_services().values())[:3]:
                    config = service.get_config()
                    suggestions.extend(config.keywords[:2])

                suggestion_text = ', '.join([f"`{s}`" for s in suggestions])

                self.send_message(
                    f"🤔 Không hiểu '{text}'\n\n💡 **Thử:** {suggestion_text}\n\n❓ Hoặc gõ `help` để xem tất cả commands",
                    parse_mode="Markdown"
                )

        except Exception as e:
            print(f"Error handling message: {e}")
            self.send_message("❌ Có lỗi xảy ra khi xử lý tin nhắn")

    def start_polling(self):
        """Start bot polling loop"""
        print("🤖 Starting Enhanced Telegram Chatbot...")
        print(f"🔧 Loaded {len(self.service_registry.get_all_services())} services")

        if not self.bot_token or not self.chat_id:
            print("❌ Missing BOT_TOKEN or CHAT_ID")
            return

        # Send startup message with service count
        services_count = len(self.service_registry.get_all_services())
        startup_msg = f"""🤖 **Enhanced Chatbot Started!**

🔧 **Services:** {services_count} available
💬 Send `help` for commands
📋 Send `list` for service list
🚀 Send `all` to run all services
{USER_TAG} Ready to help!"""

        self.send_message(startup_msg, parse_mode="Markdown")

        self.running = True
        error_count = 0
        max_errors = 10

        while self.running:
            try:
                updates_data = self.get_updates()

                if updates_data and updates_data.get('ok'):
                    updates = updates_data.get('result', [])

                    for update in updates:
                        self.last_update_id = update['update_id']

                        if 'message' in update:
                            self.handle_message(update['message'])

                error_count = 0
                time.sleep(1)

            except KeyboardInterrupt:
                print("\n🛑 Stopping enhanced chatbot...")
                self.running = False
                self.send_message("🛑 Chatbot stopped")

            except Exception as e:
                error_count += 1
                print(f"❌ Polling error: {e} (attempt {error_count}/{max_errors})")

                if error_count >= max_errors:
                    print("💀 Too many errors, stopping bot")
                    self.send_message("❌ Bot encountering too many errors, stopping...")
                    break

                time.sleep(min(5 * error_count, 30))  # Exponential backoff

    def stop(self):
        """Stop the bot"""
        self.running = False


# Add to existing telegram_chatbot.py - Enhanced message handling for KMS

def handle_message(self, message):
    """Enhanced handle_message with KMS support"""
    try:
        text = message.get('text', '')
        user = message.get('from', {})
        username = user.get('username', user.get('first_name', 'Unknown'))

        print(f"📨 Message from {username}: {text}")

        # Parse KMS commands specifically
        if self.is_kms_command(text):
            self.handle_kms_command(text)
            return

        # Existing classification logic
        action_type, action_value = self.classify_message(text)

        if action_type == 'system':
            if action_value == 'help':
                self.show_help()
            elif action_value == 'status':
                self.show_status()
            elif action_value == 'list':
                self.list_services()
            elif action_value == 'all':
                threading.Thread(target=self.execute_all_services, daemon=True).start()

        elif action_type == 'service':
            threading.Thread(target=self.execute_service, args=(action_value,), daemon=True).start()

        else:
            # Existing fallback logic
            suggestions = []
            for service in list(self.service_registry.get_all_services().values())[:3]:
                config = service.get_config()
                suggestions.extend(config.keywords[:2])

            suggestion_text = ', '.join([f"`{s}`" for s in suggestions])

            self.send_message(
                f"🤔 Không hiểu '{text}'\n\n💡 **Thử:** {suggestion_text}\n\n❓ Hoặc gõ `help` để xem tất cả commands",
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"Error handling message: {e}")
        self.send_message("❌ Có lỗi xảy ra khi xử lý tin nhắn")


def is_kms_command(self, text):
    """Check if message is a KMS command"""
    text_lower = text.lower().strip()
    kms_patterns = [
        'kms search',
        'kms recent',
        'kms stats',
        'kms categories',
        'kms create'
    ]

    return any(pattern in text_lower for pattern in kms_patterns)


def handle_kms_command(self, text):
    """Handle KMS-specific commands"""
    try:
        from services.notion_kms_service import NotionKMSService

        kms_service = NotionKMSService()
        if not kms_service.notion:
            self.send_message("❌ Notion KMS not configured", parse_mode=None)
            return

        text_lower = text.lower().strip()

        if text_lower.startswith('kms search '):
            # Extract search query
            query = text[11:].strip()  # Remove 'kms search '
            if query:
                self.send_message(f"🔍 Searching for '{query}'...", parse_mode=None)
                threading.Thread(target=kms_service.search_knowledge, args=(query,), daemon=True).start()
            else:
                self.send_message("❌ Please provide search query. Example: `kms search machine learning`",
                                  parse_mode="Markdown")

        elif text_lower == 'kms recent':
            self.send_message("📖 Getting recent notes...", parse_mode=None)
            threading.Thread(target=kms_service.get_recent_notes, daemon=True).start()

        elif text_lower == 'kms stats':
            self.send_message("📊 Calculating statistics...", parse_mode=None)
            threading.Thread(target=kms_service.get_database_stats, daemon=True).start()

        elif text_lower == 'kms categories':
            self.send_message("📁 Loading categories...", parse_mode=None)
            threading.Thread(target=kms_service.browse_categories, daemon=True).start()

        elif text_lower == 'kms create':
            self.send_message("📝 Note creation feature coming soon!", parse_mode=None)

        else:
            # Show KMS menu
            kms_service.execute()

    except Exception as e:
        print(f"KMS command error: {e}")
        self.send_message(f"❌ KMS command failed: {str(e)}", parse_mode=None)

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