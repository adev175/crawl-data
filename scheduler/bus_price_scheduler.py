# scheduler/bus_price_scheduler.py
import schedule
import time
import logging
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.crawler_bus_price import BusPriceTracker
from services.telegram_bot import send_to_telegram

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bus_scheduler.log'),
        logging.StreamHandler()
    ]
)


class BusPriceScheduler:
    def __init__(self):
        self.tracker = BusPriceTracker()
        self.last_run = None
        self.error_count = 0
        self.max_errors = 5

    def run_price_check(self):
        """Run price check with error handling"""
        try:
            logging.info("Starting scheduled price check...")
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Run the tracker
            self.tracker.run()

            # Reset error count on success
            self.error_count = 0
            self.last_run = current_time

            logging.info(f"Price check completed successfully at {current_time}")

        except Exception as e:
            self.error_count += 1
            error_msg = f"Error in scheduled price check: {str(e)}"
            logging.error(error_msg)

            # Send error notification if too many failures
            if self.error_count >= self.max_errors:
                alert_msg = f"🚨 Bus price checker failed {self.error_count} times!\n\nLast error: {error_msg}"
                send_to_telegram(alert_msg, parse_mode=None)
                logging.critical(f"Maximum error count reached: {self.error_count}")

    def health_check(self):
        """Send periodic health check"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_msg = f"🤖 Bus price bot is running\n\nTime: {current_time}\nLast run: {self.last_run or 'Never'}\nErrors: {self.error_count}/{self.max_errors}"

        send_to_telegram(status_msg, parse_mode=None)
        logging.info("Health check sent")

    def setup_schedule(self):
        """Setup the schedule"""
        # Check prices multiple times per day
        schedule.every().day.at("08:00").do(self.run_price_check)  # Morning
        schedule.every().day.at("14:00").do(self.run_price_check)  # Afternoon
        schedule.every().day.at("20:00").do(self.run_price_check)  # Evening

        # Health check once per day
        schedule.every().day.at("09:00").do(self.health_check)

        # Emergency check every 6 hours (in case of high error count)
        schedule.every(6).hours.do(self.emergency_check)

        logging.info("Schedule setup complete:")
        logging.info("- Price checks: 08:00, 14:00, 20:00 daily")
        logging.info("- Health check: 09:00 daily")
        logging.info("- Emergency check: every 6 hours")

    def emergency_check(self):
        """Emergency check when error count is high"""
        if self.error_count >= 3:
            logging.warning("Running emergency price check due to high error count")
            self.run_price_check()

    def run_scheduler(self):
        """Main scheduler loop"""
        logging.info("Starting Bus Price Scheduler...")

        # Send startup notification
        startup_msg = "🚀 Bus price scheduler started!\n\nWill check prices 3 times daily and notify of changes."
        send_to_telegram(startup_msg, parse_mode=None)

        # Setup schedule
        self.setup_schedule()

        # Run immediately on startup
        logging.info("Running initial price check...")
        self.run_price_check()

        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logging.info("Scheduler stopped by user")
            send_to_telegram("⏹️ Bus price scheduler stopped", parse_mode=None)
        except Exception as e:
            error_msg = f"🚨 Scheduler crashed: {str(e)}"
            logging.critical(error_msg)
            send_to_telegram(error_msg, parse_mode=None)


def run_once():
    """Run price check once (for testing)"""
    logging.info("Running single price check...")
    scheduler = BusPriceScheduler()
    scheduler.run_price_check()


def main():
    """Main function with command line options"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "once":
            run_once()
        elif sys.argv[1] == "health":
            scheduler = BusPriceScheduler()
            scheduler.health_check()
        else:
            print("Usage:")
            print("  python bus_price_scheduler.py          # Run scheduler")
            print("  python bus_price_scheduler.py once     # Run once")
            print("  python bus_price_scheduler.py health   # Health check")
    else:
        scheduler = BusPriceScheduler()
        scheduler.run_scheduler()


if __name__ == "__main__":
    main()