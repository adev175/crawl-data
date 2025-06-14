# services/ai_news_service.py
from services.service_registry import BaseService, ServiceConfig


class AINewsService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="ai_news",
            description="Latest AI news from CNBC",
            keywords=["ai", "ai news", "tin ai", "news", "tin tức", "tech news", "cnbc"],
            emoji="🤖",
            category="news",
            requires_env=["BOT_TOKEN", "CHAT_ID"]
        )

    def execute(self) -> bool:
        try:
            from crawler.crawler_ai_news import run_ai_bot
            run_ai_bot()
            return True
        except Exception as e:
            print(f"AI News service error: {e}")
            return False
