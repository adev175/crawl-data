# main.py
import sys
import os
from datetime import datetime

# Import all bot modules
from crawler.crawl_ai_news import run_ai_bot
from crawler.crawler_bus_price_complete import BusPriceTracker
from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram


def run_gold_bot():
    """Run gold price bot"""
    print("Starting gold price bot...")
    buy_trend, data = fetch_gold_prices()
    if data:
        send_to_telegram(format_as_code_block(data))
        user_tag = os.getenv('USER_TAG', '')
        if buy_trend == 'increase':
            send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
        elif buy_trend == 'decrease':
            send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
    else:
        print(buy_trend)
    print("Gold price bot finished.")


def run_bus_bot():
    """Run bus price bot"""
    print("Starting bus price bot...")
    tracker = BusPriceTracker()
    tracker.run()
    print("Bus price bot finished.")


def show_menu():
    """Show interactive menu"""
    print("\n" + "=" * 50)
    print("🤖 TELEGRAM BOT CONTROL PANEL")
    print("=" * 50)
    print("1. Run AI News Bot")
    print("2. Run Gold Price Bot")
    print("3. Run Bus Price Bot")
    print("4. Run All Bots")
    print("5. View Bus Price Database")
    print("6. Schedule Bus Price Monitoring")
    print("7. Exit")
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


def is_interactive():
    """Check if running in interactive mode"""
    try:
        return sys.stdin.isatty()
    except:
        return False


def main():
    """Main function with interactive menu"""
    print(f"🚀 Starting Telegram Bot Suite - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check if running with command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "ai":
            run_ai_bot()
        elif command == "gold":
            run_gold_bot()
        elif command == "bus":
            run_bus_bot()
        elif command == "all":
            print("=== Running all bots ===")
            run_ai_bot()
            run_gold_bot()
            run_bus_bot()
        elif command == "schedule":
            start_bus_scheduler()
        elif command == "db":
            view_bus_database()
        else:
            print("Available commands:")
            print("  python main.py ai        # Run AI news bot")
            print("  python main.py gold      # Run gold price bot")
            print("  python main.py bus       # Run bus price bot")
            print("  python main.py all       # Run all bots")
            print("  python main.py schedule  # Start bus price scheduler")
            print("  python main.py db        # View bus database")
        return

    # If not interactive (Docker), run all bots by default
    if not is_interactive():
        print("🐳 Running in Docker mode - executing all bots")
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

        print("=== Docker execution completed ===")
        return

    # Interactive mode
    while True:
        try:
            show_menu()
            choice = input("Select option (1-7): ").strip()

            if choice == "1":
                run_ai_bot()

            elif choice == "2":
                run_gold_bot()

            elif choice == "3":
                run_bus_bot()

            elif choice == "4":
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

                print("=== All bots execution completed ===")

            elif choice == "5":
                view_bus_database()

            elif choice == "6":
                start_bus_scheduler()

            elif choice == "7":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid option! Please select 1-7.")

            input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()