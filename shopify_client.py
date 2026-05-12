"""
Shopify Admin API client — real-time store data for Legacy Commerce agents.
"""

import os
import requests
from datetime import datetime, timedelta, timezone


class ShopifyClient:
    API_VERSION = "2025-01"

    def __init__(self, store_url: str = None, access_token: str = None):
        raw_url = store_url or os.environ.get("SHOPIFY_STORE_URL", "")
        self.store_url = self._normalize_url(raw_url)
        self.access_token = (
            access_token
            or os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
            or os.environ.get("SHOPIFY_API_KEY", "")  # legacy fallback
        )
        self.base_url = f"https://{self.store_url}/admin/api/{self.API_VERSION}"
        self._session = requests.Session()
        self._session.headers.update({
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        })

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Accept any Shopify URL format and return storename.myshopify.com."""
        url = url.strip().rstrip("/")
        # https://admin.shopify.com/store/STORENAME
        if "admin.shopify.com/store/" in url:
            return url.split("/store/")[-1] + ".myshopify.com"
        # Strip protocol
        url = url.replace("https://", "").replace("http://", "")
        # Add .myshopify.com if bare store name given
        if url and "." not in url:
            return f"{url}.myshopify.com"
        return url

    def is_configured(self) -> bool:
        return bool(
            self.store_url
            and self.access_token
            and self.access_token not in ("", "your_access_token_here")
        )

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = self._session.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    # ── Orders ────────────────────────────────────────────────────────────────

    def get_orders(self, days: int = 7) -> list:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        data = self._get("orders.json", {
            "status": "any",
            "created_at_min": since,
            "limit": 250,
            "fields": "id,created_at,total_price,financial_status,line_items",
        })
        return data.get("orders", [])

    def get_orders_today(self) -> list:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        data = self._get("orders.json", {
            "status": "any",
            "created_at_min": today_start,
            "limit": 250,
            "fields": "id,created_at,total_price,financial_status",
        })
        return data.get("orders", [])

    # ── Products & Inventory ──────────────────────────────────────────────────

    def get_products(self, limit: int = 250) -> list:
        data = self._get("products.json", {
            "limit": limit,
            "fields": "id,title,variants,status",
        })
        return data.get("products", [])

    def get_low_inventory(self, threshold: int = 15) -> list:
        alerts = []
        for product in self.get_products():
            for variant in product.get("variants", []):
                qty = variant.get("inventory_quantity", 0)
                if qty <= threshold:
                    alerts.append({
                        "product": product["title"],
                        "variant": variant.get("title", "Default"),
                        "quantity": qty,
                        "out_of_stock": qty == 0,
                    })
        return sorted(alerts, key=lambda x: x["quantity"])

    # ── Customers ─────────────────────────────────────────────────────────────

    def get_customer_count(self) -> int:
        return self._get("customers/count.json").get("count", 0)

    def get_new_customers_count(self, days: int = 7) -> int:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        return self._get("customers/count.json", {"created_at_min": since}).get("count", 0)

    # ── Abandoned Checkouts ───────────────────────────────────────────────────

    def get_abandoned_checkouts(self) -> list:
        return self._get("checkouts.json", {"limit": 50}).get("checkouts", [])

    # ── Store Snapshot ────────────────────────────────────────────────────────

    def get_store_snapshot(self) -> dict:
        """Pull all key metrics for agent morning briefings."""
        errors = []

        def safe(fn, default, label):
            try:
                return fn()
            except Exception as e:
                errors.append(f"{label}: {e}")
                return default

        orders_7d    = safe(lambda: self.get_orders(days=7),      [], "7d orders")
        orders_today = safe(self.get_orders_today,                 [], "today orders")
        low_inv      = safe(lambda: self.get_low_inventory(15),    [], "inventory")
        total_cust   = safe(self.get_customer_count,                0, "customers")
        new_cust     = safe(lambda: self.get_new_customers_count(7), 0, "new customers")
        abandoned    = safe(self.get_abandoned_checkouts,          [], "abandoned")

        revenue_7d    = sum(float(o.get("total_price", 0)) for o in orders_7d)
        revenue_today = sum(float(o.get("total_price", 0)) for o in orders_today)
        orders_7d_cnt = len(orders_7d)
        aov           = revenue_7d / orders_7d_cnt if orders_7d_cnt else 0

        # Top products by revenue this week
        product_revenue: dict[str, float] = {}
        for order in orders_7d:
            for item in order.get("line_items", []):
                name = item.get("title", "Unknown")
                rev  = float(item.get("price", 0)) * int(item.get("quantity", 0))
                product_revenue[name] = product_revenue.get(name, 0) + rev
        top_products = sorted(product_revenue.items(), key=lambda x: x[1], reverse=True)[:5]

        abandoned_value = sum(float(c.get("total_price", 0)) for c in abandoned)

        return {
            "generated_at":        datetime.now().strftime("%Y-%m-%d %H:%M"),
            "revenue_today":       revenue_today,
            "revenue_7d":          revenue_7d,
            "orders_today":        len(orders_today),
            "orders_7d":           orders_7d_cnt,
            "aov":                 aov,
            "top_products":        top_products,
            "low_inventory":       low_inv[:10],
            "out_of_stock_count":  sum(1 for p in low_inv if p["out_of_stock"]),
            "low_stock_count":     sum(1 for p in low_inv if not p["out_of_stock"]),
            "total_customers":     total_cust,
            "new_customers_week":  new_cust,
            "abandoned_count":     len(abandoned),
            "abandoned_value":     abandoned_value,
            "errors":              errors,
        }

    def format_briefing_context(self, snap: dict) -> str:
        low_inv = snap["low_inventory"]
        inv_lines = "\n".join(
            f"  {'🔴 OUT' if p['out_of_stock'] else '🟡 LOW'} {p['product']} "
            f"({p['variant']}): {p['quantity']} units"
            for p in low_inv[:5]
        ) or "  ✅ All products adequately stocked"

        top_lines = "\n".join(
            f"  {i+1}. {name}: ${rev:,.2f}"
            for i, (name, rev) in enumerate(snap["top_products"])
        ) or "  No sales data available"

        return (
            f"\n{'━'*40}\n"
            f"LIVE STORE DATA  ({snap['generated_at']})\n"
            f"{'━'*40}\n"
            f"REVENUE\n"
            f"  Today:          ${snap['revenue_today']:>10,.2f}  ({snap['orders_today']} orders)\n"
            f"  Last 7 days:    ${snap['revenue_7d']:>10,.2f}  ({snap['orders_7d']} orders)\n"
            f"  Avg order:      ${snap['aov']:>10,.2f}\n\n"
            f"CUSTOMERS\n"
            f"  Total:          {snap['total_customers']:>10,}\n"
            f"  New this week:  {snap['new_customers_week']:>10,}\n\n"
            f"ABANDONED CARTS\n"
            f"  Open:           {snap['abandoned_count']:>10}\n"
            f"  Value:          ${snap['abandoned_value']:>10,.2f}\n\n"
            f"TOP PRODUCTS (7-day revenue)\n{top_lines}\n\n"
            f"INVENTORY ALERTS ({snap['out_of_stock_count']} out · {snap['low_stock_count']} low)\n"
            f"{inv_lines}\n"
            f"{'━'*40}"
        )

    def format_inventory_context(self, snap: dict) -> str:
        low_inv = snap["low_inventory"]
        if not low_inv:
            return "INVENTORY: All products adequately stocked."
        lines = []
        for p in low_inv:
            status = "OUT OF STOCK" if p["out_of_stock"] else f"{p['quantity']} units left"
            lines.append(f"  {status}: {p['product']} ({p['variant']})")
        return f"INVENTORY ALERTS ({len(low_inv)} items need attention):\n" + "\n".join(lines)
