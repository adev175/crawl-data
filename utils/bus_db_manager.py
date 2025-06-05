# utils/bus_db_manager.py
import sqlite3
import json
from datetime import datetime, timedelta


class BusPriceDBManager:
    def __init__(self, db_file="bus_prices.db"):
        self.db_file = db_file

    def view_all_prices(self):
        """View all recorded prices"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, min_price, created_at, updated_at 
            FROM daily_prices 
            ORDER BY date DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        print("=== All Recorded Prices ===")
        for date, price, created, updated in results:
            print(f"{date}: ¥{price:,} (recorded: {created}, updated: {updated})")

        return results

    def view_price_changes(self):
        """View all price changes"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, old_price, new_price, change_amount, change_percentage, created_at
            FROM price_changes 
            ORDER BY created_at DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        print("\n=== Price Changes ===")
        for date, old, new, change, percentage, created in results:
            trend = "📈" if change > 0 else "📉"
            print(f"{trend} {date}: ¥{old:,} → ¥{new:,} ({change:+,} / {percentage:+.1f}%) - {created}")

        return results

    def get_price_statistics(self):
        """Get price statistics"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Overall stats
        cursor.execute('''
            SELECT 
                MIN(min_price) as lowest,
                MAX(min_price) as highest,
                AVG(min_price) as average,
                COUNT(*) as total_records
            FROM daily_prices
        ''')

        stats = cursor.fetchone()

        # Recent trend (last 7 days)
        cursor.execute('''
            SELECT min_price FROM daily_prices 
            WHERE date >= date('now', '-7 days')
            ORDER BY date
        ''')

        recent_prices = [row[0] for row in cursor.fetchall()]

        conn.close()

        print("\n=== Price Statistics ===")
        if stats and stats[0]:
            print(f"Lowest price ever: ¥{stats[0]:,}")
            print(f"Highest price ever: ¥{stats[1]:,}")
            print(f"Average price: ¥{stats[2]:,.0f}")
            print(f"Total records: {stats[3]}")

            if len(recent_prices) >= 2:
                trend = "increasing" if recent_prices[-1] > recent_prices[0] else "decreasing"
                print(f"Recent trend (7 days): {trend}")
                print(f"Recent prices: {[f'¥{p:,}' for p in recent_prices]}")

        return stats, recent_prices

    def clean_old_records(self, days_to_keep=90):
        """Clean old records (keep only recent data)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")

        # Count records to be deleted
        cursor.execute("SELECT COUNT(*) FROM daily_prices WHERE date < ?", (cutoff_date,))
        count_prices = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM price_changes WHERE created_at < ?", (cutoff_date,))
        count_changes = cursor.fetchone()[0]

        # Delete old records
        cursor.execute("DELETE FROM daily_prices WHERE date < ?", (cutoff_date,))
        cursor.execute("DELETE FROM price_changes WHERE created_at < ?", (cutoff_date,))

        conn.commit()
        conn.close()

        print(f"\n=== Cleanup Complete ===")
        print(f"Deleted {count_prices} old price records")
        print(f"Deleted {count_changes} old change records")
        print(f"Kept records from {cutoff_date} onwards")

    def export_to_json(self, filename=None):
        """Export data to JSON"""
        if not filename:
            filename = f"bus_prices_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Get all data
        cursor.execute("SELECT * FROM daily_prices ORDER BY date")
        prices = cursor.fetchall()

        cursor.execute("SELECT * FROM price_changes ORDER BY created_at")
        changes = cursor.fetchall()

        conn.close()

        # Format data
        export_data = {
            "export_date": datetime.now().isoformat(),
            "daily_prices": [
                {
                    "id": row[0],
                    "date": row[1],
                    "min_price": row[2],
                    "prices_json": row[3],
                    "created_at": row[4],
                    "updated_at": row[5]
                }
                for row in prices
            ],
            "price_changes": [
                {
                    "id": row[0],
                    "date": row[1],
                    "old_price": row[2],
                    "new_price": row[3],
                    "change_amount": row[4],
                    "change_percentage": row[5],
                    "created_at": row[6]
                }
                for row in changes
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"\n=== Export Complete ===")
        print(f"Data exported to: {filename}")
        print(f"Price records: {len(export_data['daily_prices'])}")
        print(f"Change records: {len(export_data['price_changes'])}")

    def get_price_alerts(self, threshold_percentage=10):
        """Get significant price changes"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date, old_price, new_price, change_amount, change_percentage
            FROM price_changes 
            WHERE ABS(change_percentage) >= ?
            ORDER BY ABS(change_percentage) DESC
        ''', (threshold_percentage,))

        results = cursor.fetchall()
        conn.close()

        print(f"\n=== Significant Price Changes (≥{threshold_percentage}%) ===")
        for date, old, new, change, percentage in results:
            trend = "🔺" if change > 0 else "🔻"
            print(f"{trend} {date}: ¥{old:,} → ¥{new:,} ({percentage:+.1f}%)")

        return results


def main():
    """Interactive database management"""
    manager = BusPriceDBManager()

    while True:
        print("\n" + "=" * 50)
        print("Bus Price Database Manager")
        print("=" * 50)
        print("1. View all prices")
        print("2. View price changes")
        print("3. View statistics")
        print("4. View significant changes (≥10%)")
        print("5. Clean old records (90+ days)")
        print("6. Export to JSON")
        print("7. Exit")

        try:
            choice = input("\nSelect option (1-7): ").strip()

            if choice == "1":
                manager.view_all_prices()
            elif choice == "2":
                manager.view_price_changes()
            elif choice == "3":
                manager.get_price_statistics()
            elif choice == "4":
                manager.get_price_alerts()
            elif choice == "5":
                confirm = input("Delete records older than 90 days? (y/N): ")
                if confirm.lower() == 'y':
                    manager.clean_old_records()
            elif choice == "6":
                manager.export_to_json()
            elif choice == "7":
                print("Goodbye!")
                break
            else:
                print("Invalid option!")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()