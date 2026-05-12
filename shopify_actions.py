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
