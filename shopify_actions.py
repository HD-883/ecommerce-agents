"""
Shopify write operations — real actions agents can take on the store.
"""

import os
import random
import string
from datetime import datetime, timedelta, timezone
import requests


class ShopifyActions:
    API_VERSION = "2025-01"

    def __init__(self, store_url: str = None, access_token: str = None):
        raw = store_url or os.environ.get("SHOPIFY_STORE_URL", "")
        self.store_url = self._normalize_url(raw)
        self.access_token = (
            access_token
            or os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
            or os.environ.get("SHOPIFY_API_KEY", "")
        )
        self.base_url = f"https://{self.store_url}/admin/api/{self.API_VERSION}"
        self._session = requests.Session()
        self._session.headers.update({
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        })

    @staticmethod
    def _normalize_url(url: str) -> str:
        url = url.strip().rstrip("/")
        if "admin.shopify.com/store/" in url:
            return url.split("/store/")[-1] + ".myshopify.com"
        url = url.replace("https://", "").replace("http://", "")
        if url and "." not in url:
            return f"{url}.myshopify.com"
        return url

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = self._session.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _put(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = self._session.put(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        resp = self._session.get(url, params=params or {})
        resp.raise_for_status()
        return resp.json()

    # ── Flash Sales ───────────────────────────────────────────────────────────

    def create_flash_sale(
        self,
        title: str,
        discount_percent: float,
        duration_hours: int = 6,
        usage_limit: int = None,
        code: str = None,
    ) -> dict:
        """Create a price rule + discount code for a flash sale."""
        starts = datetime.now(timezone.utc)
        ends   = starts + timedelta(hours=duration_hours)

        # Create price rule
        rule_payload = {
            "price_rule": {
                "title": title,
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": "percentage",
                "value": f"-{discount_percent}",
                "customer_selection": "all",
                "starts_at": starts.isoformat(),
                "ends_at": ends.isoformat(),
            }
        }
        if usage_limit:
            rule_payload["price_rule"]["usage_limit"] = usage_limit

        rule = self._post("price_rules.json", rule_payload)
        rule_id = rule["price_rule"]["id"]

        # Generate code if not provided
        if not code:
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            code = f"FLASH{suffix}"

        # Create discount code
        code_payload = {"discount_code": {"code": code}}
        discount = self._post(f"price_rules/{rule_id}/discount_codes.json", code_payload)

        return {
            "success": True,
            "code": code,
            "discount_percent": discount_percent,
            "starts_at": starts.strftime("%Y-%m-%d %H:%M UTC"),
            "ends_at": ends.strftime("%Y-%m-%d %H:%M UTC"),
            "duration_hours": duration_hours,
            "usage_limit": usage_limit or "unlimited",
            "price_rule_id": rule_id,
            "shopify_url": f"https://{self.store_url}/discount/{code}",
        }

    def get_active_discount_codes(self) -> list:
        """List all currently active price rules."""
        now = datetime.now(timezone.utc).isoformat()
        data = self._get("price_rules.json", {
            "limit": 50,
            "ends_at_min": now,
        })
        return data.get("price_rules", [])

    # ── Pricing ───────────────────────────────────────────────────────────────

    def get_products_with_prices(self, limit: int = 50) -> list:
        """Get products and their current prices."""
        data = self._get("products.json", {
            "limit": limit,
            "fields": "id,title,variants",
        })
        products = []
        for p in data.get("products", []):
            for v in p.get("variants", []):
                products.append({
                    "product_id": p["id"],
                    "product_title": p["title"],
                    "variant_id": v["id"],
                    "variant_title": v.get("title", "Default"),
                    "price": float(v.get("price", 0)),
                    "compare_at_price": v.get("compare_at_price"),
                    "inventory_quantity": v.get("inventory_quantity", 0),
                })
        return products

    def update_product_price(
        self, variant_id: int, new_price: float, compare_at_price: float = None
    ) -> dict:
        """Update a variant's price. Optionally set compare_at_price for sale display."""
        payload: dict = {"variant": {"id": variant_id, "price": str(new_price)}}
        if compare_at_price is not None:
            payload["variant"]["compare_at_price"] = str(compare_at_price)
        result = self._put(f"variants/{variant_id}.json", payload)
        v = result.get("variant", {})
        return {
            "success": True,
            "variant_id": variant_id,
            "new_price": v.get("price"),
            "compare_at_price": v.get("compare_at_price"),
        }

    # ── Abandoned Checkouts ───────────────────────────────────────────────────

    def get_abandoned_checkout_details(self) -> list:
        """Get abandoned checkouts with customer + cart details."""
        data = self._get("checkouts.json", {"limit": 50})
        results = []
        for c in data.get("checkouts", []):
            customer = c.get("customer") or {}
            line_items = c.get("line_items", [])
            results.append({
                "checkout_id": c.get("token"),
                "created_at": c.get("created_at", ""),
                "total_price": float(c.get("total_price", 0)),
                "customer_email": customer.get("email", "guest"),
                "customer_name": f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Guest",
                "item_count": len(line_items),
                "items": [
                    {"title": i.get("title"), "price": i.get("price"), "quantity": i.get("quantity")}
                    for i in line_items[:3]
                ],
                "recovery_url": c.get("abandoned_checkout_url", ""),
            })
        return results

    # ── Product Creation ──────────────────────────────────────────────────────

    def create_product(
        self,
        title: str,
        description: str,
        price: float,
        product_type: str = "",
        tags: list[str] = None,
        vendor: str = "Legacy Commerce",
        compare_at_price: float = None,
        sku: str = None,
        weight_grams: int = 200,
        images: list[str] = None,
    ) -> dict:
        """Create a new product listing on Shopify."""
        variant: dict = {
            "price": str(price),
            "inventory_management": "shopify",
            "inventory_quantity": 999,
            "weight": weight_grams,
            "weight_unit": "g",
            "fulfillment_service": "manual",
        }
        if compare_at_price:
            variant["compare_at_price"] = str(compare_at_price)
        if sku:
            variant["sku"] = sku

        payload: dict = {
            "product": {
                "title": title,
                "body_html": description,
                "vendor": vendor,
                "product_type": product_type,
                "tags": ", ".join(tags or []),
                "status": "active",
                "variants": [variant],
            }
        }
        if images:
            payload["product"]["images"] = [{"src": url} for url in images[:5]]

        result = self._post("products.json", payload)
        p = result.get("product", {})
        variant_data = p.get("variants", [{}])[0]
        return {
            "success": True,
            "product_id": p.get("id"),
            "title": p.get("title"),
            "handle": p.get("handle"),
            "status": p.get("status"),
            "variant_id": variant_data.get("id"),
            "price": variant_data.get("price"),
            "shopify_url": f"https://{self.store_url}/products/{p.get('handle')}",
            "admin_url": f"https://{self.store_url}/admin/products/{p.get('id')}",
        }

    def get_collections(self) -> list:
        """List all custom collections."""
        data = self._get("custom_collections.json", {"limit": 50})
        return [
            {"id": c["id"], "title": c["title"], "handle": c["handle"]}
            for c in data.get("custom_collections", [])
        ]

    def add_product_to_collection(self, product_id: int, collection_id: int) -> dict:
        """Add a product to a collection."""
        payload = {"collect": {"product_id": product_id, "collection_id": collection_id}}
        result = self._post("collects.json", payload)
        return {"success": True, "collect_id": result.get("collect", {}).get("id")}

    # ── Draft Orders ──────────────────────────────────────────────────────────

    def create_draft_order(
        self,
        line_items: list,
        customer_email: str = None,
        note: str = None,
        discount_code: str = None,
    ) -> dict:
        """Create a draft order (e.g. for a VIP manual offer)."""
        payload: dict = {"draft_order": {"line_items": line_items}}
        if customer_email:
            payload["draft_order"]["email"] = customer_email
        if note:
            payload["draft_order"]["note"] = note
        if discount_code:
            payload["draft_order"]["applied_discount"] = {
                "value_type": "percentage",
                "value": "10",
                "title": discount_code,
            }
        result = self._post("draft_orders.json", payload)
        d = result.get("draft_order", {})
        return {
            "success": True,
            "draft_order_id": d.get("id"),
            "invoice_url": d.get("invoice_url"),
            "total_price": d.get("total_price"),
        }

    # ── Product Images ────────────────────────────────────────────────────────

    def add_product_images(self, product_id: int, image_urls: list[str]) -> dict:
        """Add images to an existing Shopify product by URL."""
        added = []
        for url in image_urls[:5]:
            try:
                result = self._post(
                    f"products/{product_id}/images.json",
                    {"image": {"src": url}},
                )
                img = result.get("image", {})
                added.append({"id": img.get("id"), "src": img.get("src")})
            except Exception as e:
                added.append({"error": str(e), "url": url})
        return {"product_id": product_id, "images_added": len([i for i in added if "id" in i]), "results": added}

    def get_products_without_images(self, limit: int = 50) -> list:
        """Return products that have no images attached."""
        data = self._get("products.json", {
            "limit": limit,
            "fields": "id,title,images,product_type,tags",
        })
        return [
            {"id": p["id"], "title": p["title"], "product_type": p.get("product_type", ""), "tags": p.get("tags", "")}
            for p in data.get("products", [])
            if not p.get("images")
        ]

    # ── Analytics (CIPHER) ────────────────────────────────────────────────────

    def get_revenue_by_day(self, days: int = 30) -> dict:
        """Daily revenue breakdown for the last N days."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        data  = self._get("orders.json", {
            "status": "any",
            "financial_status": "paid",
            "created_at_min": since,
            "limit": 250,
            "fields": "created_at,total_price",
        })
        daily: dict[str, float] = {}
        for order in data.get("orders", []):
            day = order["created_at"][:10]
            daily[day] = daily.get(day, 0.0) + float(order.get("total_price", 0))

        total    = sum(daily.values())
        avg_day  = total / days if days else 0
        best_day = max(daily.items(), key=lambda x: x[1]) if daily else ("—", 0)
        return {
            "period_days":   days,
            "total_revenue": round(total, 2),
            "avg_daily":     round(avg_day, 2),
            "best_day":      best_day[0],
            "best_day_rev":  round(best_day[1], 2),
            "daily_breakdown": {k: round(v, 2) for k, v in sorted(daily.items())},
            "days_with_sales": len(daily),
        }

    def get_top_products_by_revenue(self, days: int = 30, limit: int = 10) -> list:
        """Top products by revenue over the last N days."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        data  = self._get("orders.json", {
            "status": "any",
            "financial_status": "paid",
            "created_at_min": since,
            "limit": 250,
            "fields": "line_items",
        })
        product_stats: dict[str, dict] = {}
        for order in data.get("orders", []):
            for item in order.get("line_items", []):
                title = item.get("title", "Unknown")
                qty   = int(item.get("quantity", 0))
                rev   = float(item.get("price", 0)) * qty
                if title not in product_stats:
                    product_stats[title] = {"revenue": 0.0, "units_sold": 0, "orders": 0}
                product_stats[title]["revenue"]    += rev
                product_stats[title]["units_sold"] += qty
                product_stats[title]["orders"]     += 1

        ranked = sorted(product_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)
        return [
            {
                "rank":        i + 1,
                "product":     title,
                "revenue":     round(stats["revenue"], 2),
                "units_sold":  stats["units_sold"],
                "avg_price":   round(stats["revenue"] / stats["units_sold"], 2) if stats["units_sold"] else 0,
            }
            for i, (title, stats) in enumerate(ranked[:limit])
        ]

    def get_conversion_funnel(self) -> dict:
        """Orders vs abandoned carts — basic conversion funnel metrics."""
        now   = datetime.now(timezone.utc)
        since = (now - timedelta(days=30)).isoformat()

        orders_data    = self._get("orders.json",   {"status": "any", "created_at_min": since, "limit": 250, "fields": "id,financial_status"})
        abandoned_data = self._get("checkouts.json",{"limit": 50})

        paid_orders = [o for o in orders_data.get("orders", []) if o.get("financial_status") == "paid"]
        abandoned   = abandoned_data.get("checkouts", [])

        total_intent   = len(paid_orders) + len(abandoned)
        conversion_pct = (len(paid_orders) / total_intent * 100) if total_intent else 0
        recovery_opp   = sum(float(c.get("total_price", 0)) for c in abandoned)

        return {
            "period_days":           30,
            "completed_orders":      len(paid_orders),
            "abandoned_carts":       len(abandoned),
            "total_checkout_intent": total_intent,
            "conversion_rate_pct":   round(conversion_pct, 1),
            "abandoned_value_usd":   round(recovery_opp, 2),
            "potential_if_50pct_recovered": round(recovery_opp * 0.5, 2),
        }

    def get_channel_snapshot(self) -> dict:
        """High-level store health for CIPHER's weekly report."""
        since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        since_7d  = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

        orders_30d = self._get("orders.json", {"status": "any", "financial_status": "paid",
                                               "created_at_min": since_30d, "limit": 250,
                                               "fields": "total_price,created_at"}).get("orders", [])
        orders_7d  = [o for o in orders_30d if o["created_at"] >= since_7d]

        rev_30d = sum(float(o["total_price"]) for o in orders_30d)
        rev_7d  = sum(float(o["total_price"]) for o in orders_7d)
        aov     = rev_30d / len(orders_30d) if orders_30d else 0

        cust_total = self._get("customers/count.json").get("count", 0)
        cust_new   = self._get("customers/count.json", {"created_at_min": since_30d}).get("count", 0)

        return {
            "revenue_last_30d":  round(rev_30d, 2),
            "revenue_last_7d":   round(rev_7d, 2),
            "orders_last_30d":   len(orders_30d),
            "orders_last_7d":    len(orders_7d),
            "avg_order_value":   round(aov, 2),
            "total_customers":   cust_total,
            "new_customers_30d": cust_new,
            "repeat_rate_est":   round(((cust_total - cust_new) / cust_total * 100), 1) if cust_total else 0,
        }
