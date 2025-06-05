# main.py
from crawler.crawl_ai_news import run_ai_bot
from crawler.crawler_bus_price import fetch_cheapest_bus_price
# from crawler.crawler_gold import main as run_gold_bot

def main():
    print("=== Running all bots ===")
    run_ai_bot()
    # run_gold_bot()
    fetch_cheapest_bus_price()

if __name__ == "__main__":
    main()
