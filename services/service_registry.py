# services/service_registry.py
import os
import importlib
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class ServiceConfig:
    """Configuration for a service"""
    name: str
    description: str
    keywords: List[str]
    emoji: str
    category: str
    enabled: bool = True
    requires_env: List[str] = None


class BaseService(ABC):
    """Base class for all services"""

    @abstractmethod
    def get_config(self) -> ServiceConfig:
        """Return service configuration"""
        pass

    @abstractmethod
    def execute(self) -> bool:
        """Execute the service. Return True if successful"""
        pass

    def validate_environment(self) -> bool:
        """Validate required environment variables"""
        config = self.get_config()
        if not config.requires_env:
            return True

        missing = []
        for env_var in config.requires_env:
            if not os.getenv(env_var):
                missing.append(env_var)

        if missing:
            print(f"❌ {config.name} missing env vars: {missing}")
            return False
        return True


class ServiceRegistry:
    """Registry for managing all bot services"""

    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.load_services()

    def load_services(self):
        """Dynamically load all services from services directory"""
        services_dir = os.path.dirname(__file__)

        # Built-in services
        self.register_builtin_services()

        # Auto-discover services in services/ directory
        for file in os.listdir(services_dir):
            if file.endswith('_service.py') and not file.startswith('_'):
                module_name = file[:-3]  # Remove .py
                try:
                    module = importlib.import_module(f'services.{module_name}')

                    # Look for service classes
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                                issubclass(attr, BaseService) and
                                attr != BaseService):
                            service_instance = attr()
                            config = service_instance.get_config()
                            self.services[config.name] = service_instance
                            print(f"✅ Loaded service: {config.name}")

                except Exception as e:
                    print(f"❌ Failed to load {module_name}: {e}")

    def register_builtin_services(self):
        """Register built-in services"""
        from services.ai_news_service import AINewsService
        from services.gold_price_service import GoldPriceService
        from services.bus_price_service import BusPriceService
        from services.notion_kms_service import NotionKMSService

        builtin_services = [
            AINewsService(),
            GoldPriceService(),
            BusPriceService(),
            NotionKMSService()
        ]

        for service in builtin_services:
            config = service.get_config()
            self.services[config.name] = service

    def get_service_by_keyword(self, text: str) -> BaseService:
        """Find service by keyword in user message"""
        text_lower = text.lower().strip()

        for service in self.services.values():
            config = service.get_config()
            if not config.enabled:
                continue

            for keyword in config.keywords:
                if keyword.lower() in text_lower:
                    return service

        return None

    def get_all_services(self) -> Dict[str, BaseService]:
        """Get all registered services"""
        return {name: service for name, service in self.services.items()
                if service.get_config().enabled}

    def get_services_by_category(self, category: str) -> Dict[str, BaseService]:
        """Get services by category"""
        return {name: service for name, service in self.services.items()
                if service.get_config().category == category and service.get_config().enabled}

    def execute_service(self, service_name: str) -> bool:
        """Execute a service by name"""
        if service_name not in self.services:
            return False

        service = self.services[service_name]
        if not service.validate_environment():
            return False

        return service.execute()

    def get_help_text(self) -> str:
        """Generate help text for all services"""
        categories = {}

        for service in self.services.values():
            config = service.get_config()
            if not config.enabled:
                continue

            if config.category not in categories:
                categories[config.category] = []
            categories[config.category].append(config)

        help_text = "🤖 **Available Services:**\n\n"

        for category, configs in categories.items():
            help_text += f"**{category.title()}:**\n"
            for config in configs:
                keywords_text = ', '.join([f'`{k}`' for k in config.keywords[:3]])
                help_text += f"{config.emoji} **{config.name}**\n"
                help_text += f"   Keywords: {keywords_text}\n"
                help_text += f"   → {config.description}\n\n"

        help_text += "💡 **Tips:**\n"
        help_text += "• Just type any keyword to trigger the service\n"
        help_text += "• Example: 'bus' → Auto check bus prices\n"
        help_text += "• Type 'all' to run all services\n"

        return help_text


# Global registry instance
registry = ServiceRegistry()