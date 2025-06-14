# services/notion_kms_service.py
import os
from datetime import datetime
from notion_client import Client
from services.service_registry import BaseService, ServiceConfig
from services.telegram_bot import send_to_telegram


class NotionKMSService(BaseService):
    def get_config(self) -> ServiceConfig:
        return ServiceConfig(
            name="notion_kms",
            description="Notion Knowledge Management System",
            keywords=["kms", "knowledge", "notion", "note", "search", "notes"],
            emoji="🧠",
            category="productivity",
            requires_env=["BOT_TOKEN", "CHAT_ID", "NOTION_TOKEN", "NOTION_KNOWLEDGE_DB"]
        )

    def __init__(self):
        self.notion = None
        self.db_id = None
        self._init_notion()

    def _init_notion(self):
        """Initialize Notion client"""
        try:
            token = os.getenv("NOTION_TOKEN")
            self.db_id = os.getenv("NOTION_KNOWLEDGE_DB")

            if token and self.db_id:
                self.notion = Client(auth=token)
                print("✅ Notion client initialized")
            else:
                print("❌ Missing NOTION_TOKEN or NOTION_KNOWLEDGE_DB")
        except Exception as e:
            print(f"❌ Failed to initialize Notion: {e}")

    def execute(self) -> bool:
        """Main entry point - show KMS menu"""
        try:
            if not self.notion:
                send_to_telegram("❌ Notion KMS not configured properly", parse_mode=None)
                return False

            menu_text = """🧠 **Notion Knowledge Management**

**Quick Commands:**
• `kms search [query]` - Search knowledge base
• `kms recent` - View recent notes (5 latest)
• `kms stats` - Database statistics
• `kms categories` - Browse by categories
• `kms create` - Create new note (coming soon)

**Examples:**
• `kms search machine learning`
• `kms search tech python`
• `kms recent`

Type any command above to get started! 🚀"""

            send_to_telegram(menu_text, parse_mode="Markdown")
            return True

        except Exception as e:
            print(f"KMS service error: {e}")
            send_to_telegram(f"❌ KMS Error: {str(e)}", parse_mode=None)
            return False

    def search_knowledge(self, query):
        """Search knowledge base by query"""
        try:
            print(f"🔍 Searching for: {query}")

            # Search in Notion database
            results = self.notion.databases.query(
                database_id=self.db_id,
                filter={
                    "or": [
                        {
                            "property": "Title",
                            "title": {
                                "contains": query
                            }
                        },
                        {
                            "property": "Content",
                            "rich_text": {
                                "contains": query
                            }
                        }
                    ]
                },
                sorts=[
                    {
                        "property": "Updated",
                        "direction": "descending"
                    }
                ],
                page_size=10
            )

            if not results["results"]:
                send_to_telegram(f"🔍 No results found for '{query}'", parse_mode=None)
                return False

            # Format results
            message = f"🔍 **Search Results for '{query}'**\n\n"

            for i, page in enumerate(results["results"][:5], 1):
                title = self._get_title(page)
                category = self._get_category(page)
                tags = self._get_tags(page)
                updated = self._get_date(page, "Updated")
                page_url = page.get("url", "")

                message += f"**{i}. {title}**\n"
                if category:
                    message += f"📁 {category}"
                if tags:
                    message += f" • 🏷️ {', '.join(tags[:3])}"
                message += f"\n📅 {updated}\n"
                message += f"🔗 [Open in Notion]({page_url})\n\n"

            if len(results["results"]) > 5:
                message += f"... and {len(results['results']) - 5} more results"

            send_to_telegram(message, parse_mode="Markdown")
            return True

        except Exception as e:
            print(f"Search error: {e}")
            send_to_telegram(f"❌ Search failed: {str(e)}", parse_mode=None)
            return False

    def get_recent_notes(self, limit=5):
        """Get recent notes from knowledge base"""
        try:
            print(f"📖 Getting {limit} recent notes...")

            results = self.notion.databases.query(
                database_id=self.db_id,
                sorts=[
                    {
                        "property": "Updated",
                        "direction": "descending"
                    }
                ],
                page_size=limit
            )

            if not results["results"]:
                send_to_telegram("📭 No notes found in knowledge base", parse_mode=None)
                return False

            message = f"📖 **Recent Notes ({len(results['results'])})**\n\n"

            for i, page in enumerate(results["results"], 1):
                title = self._get_title(page)
                category = self._get_category(page)
                updated = self._get_date(page, "Updated")
                page_url = page.get("url", "")

                message += f"**{i}. {title}**\n"
                if category:
                    message += f"📁 {category} • "
                message += f"📅 {updated}\n"
                message += f"🔗 [Open]({page_url})\n\n"

            send_to_telegram(message, parse_mode="Markdown")
            return True

        except Exception as e:
            print(f"Recent notes error: {e}")
            send_to_telegram(f"❌ Failed to get recent notes: {str(e)}", parse_mode=None)
            return False

    def get_database_stats(self):
        """Get knowledge base statistics"""
        try:
            print("📊 Getting database statistics...")

            # Get all pages for statistics
            all_results = []
            has_more = True
            next_cursor = None

            while has_more:
                query_params = {
                    "database_id": self.db_id,
                    "page_size": 100
                }
                if next_cursor:
                    query_params["start_cursor"] = next_cursor

                results = self.notion.databases.query(**query_params)
                all_results.extend(results["results"])

                has_more = results["has_more"]
                next_cursor = results.get("next_cursor")

            # Analyze data
            total_notes = len(all_results)
            categories = {}
            tags = {}

            for page in all_results:
                # Count categories
                category = self._get_category(page)
                if category:
                    categories[category] = categories.get(category, 0) + 1

                # Count tags
                page_tags = self._get_tags(page)
                for tag in page_tags:
                    tags[tag] = tags.get(tag, 0) + 1

            # Format statistics
            message = f"📊 **Knowledge Base Statistics**\n\n"
            message += f"📚 **Total Notes:** {total_notes}\n\n"

            if categories:
                message += "📁 **Categories:**\n"
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    message += f"• {cat}: {count} notes\n"
                message += "\n"

            if tags:
                message += "🏷️ **Top Tags:**\n"
                top_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)[:5]
                for tag, count in top_tags:
                    message += f"• {tag}: {count} notes\n"

            send_to_telegram(message, parse_mode="Markdown")
            return True

        except Exception as e:
            print(f"Stats error: {e}")
            send_to_telegram(f"❌ Failed to get statistics: {str(e)}", parse_mode=None)
            return False

    def browse_categories(self):
        """Browse notes by categories"""
        try:
            print("📁 Browsing categories...")

            # Get all pages to analyze categories
            results = self.notion.databases.query(
                database_id=self.db_id,
                page_size=100
            )

            categories = {}
            for page in results["results"]:
                category = self._get_category(page)
                if category:
                    if category not in categories:
                        categories[category] = []
                    title = self._get_title(page)
                    url = page.get("url", "")
                    categories[category].append({"title": title, "url": url})

            if not categories:
                send_to_telegram("📁 No categories found", parse_mode=None)
                return False

            message = "📁 **Browse by Categories**\n\n"

            for category, notes in categories.items():
                message += f"**📁 {category} ({len(notes)} notes)**\n"
                for i, note in enumerate(notes[:3], 1):
                    message += f"{i}. [{note['title']}]({note['url']})\n"
                if len(notes) > 3:
                    message += f"... and {len(notes) - 3} more\n"
                message += "\n"

            send_to_telegram(message, parse_mode="Markdown")
            return True

        except Exception as e:
            print(f"Browse categories error: {e}")
            send_to_telegram(f"❌ Failed to browse categories: {str(e)}", parse_mode=None)
            return False

    # Helper methods
    def _get_title(self, page):
        """Extract title from page"""
        try:
            title_prop = page["properties"].get("Title", {})
            if title_prop.get("title"):
                return title_prop["title"][0]["plain_text"]
            return "Untitled"
        except:
            return "Untitled"

    def _get_category(self, page):
        """Extract category from page"""
        try:
            category_prop = page["properties"].get("Category", {})
            if category_prop.get("select"):
                return category_prop["select"]["name"]
            return None
        except:
            return None

    def _get_tags(self, page):
        """Extract tags from page"""
        try:
            tags_prop = page["properties"].get("Tags", {})
            if tags_prop.get("multi_select"):
                return [tag["name"] for tag in tags_prop["multi_select"]]
            return []
        except:
            return []

    def _get_date(self, page, property_name):
        """Extract date from page"""
        try:
            date_prop = page["properties"].get(property_name, {})
            if property_name == "Updated" and date_prop.get("last_edited_time"):
                date_str = date_prop["last_edited_time"]
            elif property_name == "Created" and date_prop.get("created_time"):
                date_str = date_prop["created_time"]
            else:
                return "Unknown"

            # Format date
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime('%d/%m/%Y')
        except:
            return "Unknown"