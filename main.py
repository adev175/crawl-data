# main.py - Updated for GitHub Actions with KMS Support
import sys
import os
from datetime import datetime

# Import all bot modules
from crawler.crawler_ai_news import run_ai_bot
from crawler.crawler_bus_price import BusPriceTracker
from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram


def run_gold_bot():
    """Run gold price bot with GitHub Actions support"""
    print("Starting gold price bot...")

    # Check if running in GitHub Actions
    if is_github_actions():
        print("Using enhanced fetcher for GitHub Actions...")
        try:
            from crawler.crawler_gold import main as enhanced_gold_main
            enhanced_gold_main()
            return
        except ImportError:
            print("Enhanced gold crawler not found, using standard version...")

    # Standard version
    try:
        from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram

        # Handle the return values properly
        result = fetch_gold_prices()

        # Check if result has 2 or 3 values
        if len(result) == 3:
            buy_trend, data, source_name = result
            print(f"✅ Data retrieved from source: {source_name}")
        else:
            buy_trend, data = result
            source_name = None

        if data:
            # Try to use the enhanced format function first
            try:
                if source_name:
                    send_to_telegram(format_as_code_block(data, source_name))
                else:
                    send_to_telegram(format_as_code_block(data))
            except TypeError:
                # Fallback: format_as_code_block only accepts 1 argument
                send_to_telegram(format_as_code_block(data))
                if source_name:
                    send_to_telegram(f"📊 Nguồn: {source_name}", parse_mode=None)

            user_tag = os.getenv('USER_TAG', '')
            if buy_trend == 'increase':
                send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
            elif buy_trend == 'decrease':
                send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
            else:
                send_to_telegram(f"📊 Giá vàng cập nhật thành công!", parse_mode=None)
        else:
            print("No gold data retrieved")
            send_to_telegram("❌ Không thể lấy giá vàng hôm nay", parse_mode=None)

    except Exception as e:
        print(f"Gold bot error: {e}")
        # Send error notification
        try:
            from services.telegram_bot import send_to_telegram
            send_to_telegram(f"❌ Lỗi gold bot: {str(e)[:100]}...", parse_mode=None)
        except:
            pass

    print("Gold price bot finished.")


def run_bus_bot():
    """Run bus price bot with fallback support"""
    print("Starting bus price bot...")

    try:
        # Try stable version first
        from crawler.stable_bus_crawler import StableBusPriceTracker
        tracker = StableBusPriceTracker()
        success = tracker.run()

        if not success:
            print("⚠️ Stable tracker failed, trying original version...")
            # Fallback to original
            from crawler.crawler_bus_price import BusPriceTracker
            original_tracker = BusPriceTracker()
            original_tracker.run()

    except Exception as e:
        print(f"❌ All bus tracking methods failed: {e}")
        # Send error notification
        try:
            from services.telegram_bot import send_to_telegram
            send_to_telegram(f"❌ Bus bot error: {str(e)[:100]}...", parse_mode=None)
        except:
            pass

    print("Bus price bot finished.")


def run_kms_bot():
    """Run KMS bot"""
    print("Starting KMS bot...")

    try:
        from services.notion_kms_service import NotionKMSService
        kms_service = NotionKMSService()

        if kms_service.execute():
            print("✅ KMS Bot completed successfully")
        else:
            print("❌ KMS Bot completed with errors")

    except Exception as e:
        print(f"❌ KMS bot error: {e}")
        try:
            from services.telegram_bot import send_to_telegram
            send_to_telegram(f"❌ Lỗi KMS bot: {str(e)[:100]}...", parse_mode=None)
        except:
            pass

    print("KMS bot finished.")


def is_github_actions():
    """Check if running in GitHub Actions"""
    return os.getenv('GITHUB_ACTIONS') == 'true'


def is_interactive():
    """Check if running in interactive mode"""
    try:
        return sys.stdin.isatty() and not is_github_actions()
    except:
        return False


def show_menu():
    """Show interactive menu"""
    print("\n" + "=" * 50)
    print("🤖 TELEGRAM BOT CONTROL PANEL")
    print("=" * 50)
    print("1. Run AI News Bot")
    print("2. Run Gold Price Bot")
    print("3. Run Bus Price Bot")
    print("4. Run KMS Bot")
    print("5. Run All Bots")
    print("6. View Bus Price Database")
    print("7. Schedule Bus Price Monitoring")
    print("8. Start Interactive Chatbot")
    print("9. Chatbot Manager")
    print("10. Exit")
    print("-" * 50)


def view_bus_database():
    """View bus price database"""
    try:
        from utils.bus_db_manager import BusPriceDBManager
        manager = BusPriceDBManager()

        print("\n=== Bus Price Database Summary ===")
        stats, recent = manager.get_price_statistics()
        print("\n=== Recent Price Changes ===")
        changes = manager.view_price_changes()

        if not changes:
            print("No price changes recorded yet.")

    except Exception as e:
        print(f"Error accessing database: {e}")


def start_bus_scheduler():
    """Start bus price scheduler"""
    try:
        from scheduler.bus_price_scheduler import BusPriceScheduler
        print("Starting bus price scheduler...")
        print("This will run continuously and check prices 3 times daily.")
        print("Press Ctrl+C to stop.")

        scheduler = BusPriceScheduler()
        scheduler.run_scheduler()

    except KeyboardInterrupt:
        print("\nScheduler stopped.")
    except Exception as e:
        print(f"Scheduler error: {e}")


def main():
    """Main function with GitHub Actions support"""
    print(f"🚀 Starting Telegram Bot Suite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # GitHub Actions mode
    if is_github_actions():
        print("🐙 Running in GitHub Actions mode")

    # Check if running with command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        try:
            if command == "ai":
                run_ai_bot()
            elif command == "gold":
                run_gold_bot()
            elif command == "bus":
                run_bus_bot()
            elif command == "kms":
                run_kms_bot()
            elif command == "all":
                print("=== Running all bots ===")
                run_ai_bot()
                run_gold_bot()
                run_bus_bot()
                run_kms_bot()
            elif command == "schedule":
                start_bus_scheduler()
            elif command == "db":
                view_bus_database()
            elif command == "chatbot":
                # Start interactive chatbot
                from telegram_chatbot import TelegramChatBot
                bot = TelegramChatBot()
                bot.start_polling()
            else:
                print("Available commands:")
                print("  python main.py ai        # Run AI news bot")
                print("  python main.py gold      # Run gold price bot")
                print("  python main.py bus       # Run bus price bot")
                print("  python main.py kms       # Run KMS bot")
                print("  python main.py all       # Run all bots")
                print("  python main.py schedule  # Start bus price scheduler")
                print("  python main.py db        # View bus database")
                print("  python main.py chatbot   # Start interactive chatbot")

        except Exception as e:
            print(f"❌ Error running {command}: {e}")
            # Don't exit with error code in GitHub Actions to avoid failing the workflow
            if not is_github_actions():
                sys.exit(1)
        return

    # If not interactive (Docker or GitHub Actions), run all bots by default
    if not is_interactive():
        print("🤖 Running in non-interactive mode - executing all bots")
        try:
            run_ai_bot()
            print("✅ AI News Bot completed")
        except Exception as e:
            print(f"❌ AI News Bot failed: {e}")

        try:
            run_gold_bot()
            print("✅ Gold Price Bot completed")
        except Exception as e:
            print(f"❌ Gold Price Bot failed: {e}")

        try:
            run_bus_bot()
            print("✅ Bus Price Bot completed")
        except Exception as e:
            print(f"❌ Bus Price Bot failed: {e}")

        try:
            run_kms_bot()
            print("✅ KMS Bot completed")
        except Exception as e:
            print(f"❌ KMS Bot failed: {e}")

        print("=== Execution completed ===")
        return

    # Interactive mode
    while True:
        try:
            show_menu()
            choice = input("Select option (1-10): ").strip()

            if choice == "1":
                run_ai_bot()

            elif choice == "2":
                run_gold_bot()

            elif choice == "3":
                run_bus_bot()

            elif choice == "4":
                run_kms_bot()

            elif choice == "5":
                print("\n=== Running All Bots ===")
                try:
                    run_ai_bot()
                    print("✅ AI News Bot completed")
                except Exception as e:
                    print(f"❌ AI News Bot failed: {e}")

                try:
                    run_gold_bot()
                    print("✅ Gold Price Bot completed")
                except Exception as e:
                    print(f"❌ Gold Price Bot failed: {e}")

                try:
                    run_bus_bot()
                    print("✅ Bus Price Bot completed")
                except Exception as e:
                    print(f"❌ Bus Price Bot failed: {e}")

                try:
                    run_kms_bot()
                    print("✅ KMS Bot completed")
                except Exception as e:
                    print(f"❌ KMS Bot failed: {e}")

                print("=== All bots execution completed ===")

            elif choice == "6":
                view_bus_database()

            elif choice == "7":
                start_bus_scheduler()

            elif choice == "8":
                # Start interactive chatbot
                try:
                    from telegram_chatbot import TelegramChatBot
                    print("🤖 Starting interactive chatbot...")
                    print("💬 Users can now message the bot to trigger commands!")
                    print("⏹️  Press Ctrl+C to stop chatbot")

                    bot = TelegramChatBot()
                    bot.start_polling()
                except KeyboardInterrupt:
                    print("\n🛑 Chatbot stopped")
                except Exception as e:
                    print(f"❌ Chatbot error: {e}")

            elif choice == "9":
                # Chatbot manager
                try:
                    from chatbot_manager import ChatbotManager
                    manager = ChatbotManager()
                    manager.interactive_menu()
                except Exception as e:
                    print(f"❌ Chatbot manager error: {e}")

            elif choice == "10":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid option! Please select 1-10.")

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()