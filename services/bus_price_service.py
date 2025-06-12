# services/bus_price_service.py
from services.service_registry import BaseService, ServiceConfig


class BusPriceService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="bus_price",
            description="Bus prices Nagaoka → Shinjuku",
            keywords=["bus", "xe", "xe buýt", "bus time", "bus price", "giá xe", "nagaoka", "shinjuku"],
            emoji="🚌",
            category="transport",
            requires_env=["BOT_TOKEN", "CHAT_ID", "TARGET_URL"]
        )

    def execute(self) -> bool:
        try:
            # Try stable version first
            try:
                from crawler.stable_bus_crawler import StableBusPriceTracker
                tracker = StableBusPriceTracker()
                success = tracker.run()
                if success:
                    return True
            except ImportError:
                pass

            # Fallback to original version
            from crawler.crawler_bus_price_complete import BusPriceTracker
            tracker = BusPriceTracker()
            tracker.run()
            return True

        except Exception as e:
            print(f"Bus price service error: {e}")
            return False