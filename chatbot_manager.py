# chatbot_manager.py
import os
import sys
import time
import signal
import threading
from datetime import datetime


class ChatbotManager:
    def __init__(self):
        self.chatbot = None
        self.chatbot_thread = None
        self.is_running = False

    def start_chatbot(self):
        """Start the chatbot in background"""
        if self.is_running:
            print("⚠️  Chatbot is already running!")
            return

        try:
            from telegram_chatbot import TelegramChatBot

            self.chatbot = TelegramChatBot()
            self.chatbot_thread = threading.Thread(target=self.chatbot.start_polling, daemon=True)
            self.chatbot_thread.start()
            self.is_running = True

            print("✅ Chatbot started successfully!")
            print("💬 Users can now send messages to trigger bots")
            print("⏹️  Press Ctrl+C to stop")

        except Exception as e:
            print(f"❌ Failed to start chatbot: {e}")

    def stop_chatbot(self):
        """Stop the chatbot"""
        if not self.is_running:
            print("ℹ️  Chatbot is not running")
            return

        if self.chatbot:
            self.chatbot.stop()
            self.chatbot.send_message("🛑 Chatbot stopped by admin")

        self.is_running = False
        print("🛑 Chatbot stopped")

    def show_status(self):
        """Show chatbot status"""
        status = "🟢 Running" if self.is_running else "🔴 Stopped"
        current_time = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

        print(f"""
📊 Chatbot Status: {status}
⏰ Current time: {current_time}
🤖 Bot token: {'✅ Set' if os.getenv('BOT_TOKEN') else '❌ Missing'}
💬 Chat ID: {'✅ Set' if os.getenv('CHAT_ID') else '❌ Missing'}
""")

    def test_connection(self):
        """Test Telegram connection"""
        try:
            import requests

            bot_token = os.getenv('BOT_TOKEN')
            chat_id = os.getenv('CHAT_ID')

            if not bot_token or not chat_id:
                print("❌ Missing BOT_TOKEN or CHAT_ID")
                return

            # Test bot info
            url = f"https://api.telegram.org/bot{bot_token}/getMe"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    print(f"✅ Bot connection successful!")
                    print(f"   Bot name: {bot_info.get('first_name')}")
                    print(f"   Username: @{bot_info.get('username')}")
                else:
                    print(f"❌ Bot API error: {data}")
            else:
                print(f"❌ HTTP error: {response.status_code}")

            # Test sending message
            test_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            test_data = {
                'chat_id': chat_id,
                'text': '🧪 Connection test successful!'
            }

            test_response = requests.post(test_url, data=test_data, timeout=10)
            if test_response.status_code == 200:
                print("✅ Message sending successful!")
            else:
                print(f"❌ Message sending failed: {test_response.status_code}")

        except Exception as e:
            print(f"❌ Connection test failed: {e}")

    def show_commands_help(self):
        """Show available commands for users"""
        print("""
📱 User Commands (send these to the bot):

🚌 Bus Commands:
   • "bus" / "xe" / "bus time" / "giá xe"

🪙 Gold Commands:
   • "gold" / "vàng" / "giá vàng"

🤖 AI News Commands:
   • "ai" / "news" / "tin ai"

🚀 Other Commands:
   • "all" / "tất cả" → Run all bots
   • "status" / "ping" → Check bot status
   • "help" → Show help menu

Users just need to send any of these keywords to the bot!
""")

    def interactive_menu(self):
        """Interactive menu for managing chatbot"""
        while True:
            print("\n" + "=" * 50)
            print("🤖 TELEGRAM CHATBOT MANAGER")
            print("=" * 50)
            print("1. Start Chatbot")
            print("2. Stop Chatbot")
            print("3. Show Status")
            print("4. Test Connection")
            print("5. Show User Commands")
            print("6. Run Single Bot (Manual)")
            print("7. Exit")
            print("-" * 50)

            try:
                choice = input("Select option (1-7): ").strip()

                if choice == "1":
                    self.start_chatbot()

                elif choice == "2":
                    self.stop_chatbot()

                elif choice == "3":
                    self.show_status()

                elif choice == "4":
                    self.test_connection()

                elif choice == "5":
                    self.show_commands_help()

                elif choice == "6":
                    self.manual_bot_menu()

                elif choice == "7":
                    if self.is_running:
                        self.stop_chatbot()
                    print("👋 Goodbye!")
                    break

                else:
                    print("❌ Invalid option!")

                if choice in ["1"]:  # For start chatbot, keep running
                    try:
                        while self.is_running:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        self.stop_chatbot()
                else:
                    input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                if self.is_running:
                    self.stop_chatbot()
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("Press Enter to continue...")

    def manual_bot_menu(self):
        """Manual bot execution menu"""
        print("\n🤖 Manual Bot Execution:")
        print("1. AI News Bot")
        print("2. Gold Price Bot")
        print("3. Bus Price Bot")
        print("4. All Bots")
        print("5. Back")

        choice = input("Select bot (1-5): ").strip()

        try:
            if choice == "1":
                print("🤖 Running AI News Bot...")
                from crawler.crawler_ai_news import run_ai_bot
                run_ai_bot()
                print("✅ AI News Bot completed")

            elif choice == "2":
                print("🪙 Running Gold Price Bot...")
                from main import run_gold_bot
                run_gold_bot()
                print("✅ Gold Price Bot completed")

            elif choice == "3":
                print("🚌 Running Bus Price Bot...")
                from main import run_bus_bot
                run_bus_bot()
                print("✅ Bus Price Bot completed")

            elif choice == "4":
                print("🚀 Running All Bots...")
                from main import run_ai_bot, run_gold_bot, run_bus_bot
                run_ai_bot()
                run_gold_bot()
                run_bus_bot()
                print("✅ All Bots completed")

            elif choice == "5":
                return

            else:
                print("❌ Invalid option!")

        except Exception as e:
            print(f"❌ Error running bot: {e}")


def main():
    """Main function"""
    print("🚀 Starting Telegram Chatbot Manager...")

    manager = ChatbotManager()

    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Stopping chatbot manager...")
        manager.stop_chatbot()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "start":
            manager.start_chatbot()
            try:
                while manager.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop_chatbot()

        elif command == "test":
            manager.test_connection()

        elif command == "status":
            manager.show_status()

        else:
            print("Available commands:")
            print("  python chatbot_manager.py start    # Start chatbot")
            print("  python chatbot_manager.py test     # Test connection")
            print("  python chatbot_manager.py status   # Show status")
            print("  python chatbot_manager.py          # Interactive mode")
    else:
        # Interactive mode
        manager.interactive_menu()


if __name__ == "__main__":
    main()