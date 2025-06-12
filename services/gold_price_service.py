# services/gold_price_service.py
from services.service_registry import BaseService, ServiceConfig


class GoldPriceService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="gold_price",
            description="Current gold prices in Vietnam",
            keywords=["gold", "vàng", "giá vàng", "vang", "gia vang", "sjc", "doji"],
            emoji="🪙",
            category="finance",
            requires_env=["BOT_TOKEN", "CHAT_ID"]
        )

    def execute(self) -> bool:
        try:
            import os

            from crawler.crawler_gold import fetch_gold_prices, format_as_code_block, send_to_telegram
            buy_trend, data = fetch_gold_prices()

            if data:
                send_to_telegram(format_as_code_block(data))
                user_tag = os.getenv('USER_TAG', '')
                if buy_trend == 'increase':
                    send_to_telegram(f"Có nên mua vàng không má {user_tag} 🤔🤔🤔", parse_mode=None)
                elif buy_trend == 'decrease':
                    send_to_telegram(f"✅ Mua vàng đi má {user_tag} 🧀🧀🧀", parse_mode=None)
                return True
            return False

        except Exception as e:
            print(f"Gold price service error: {e}")
            return False