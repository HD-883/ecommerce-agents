"""
Tool definitions and runner for agent actions.
Each agent gets a curated set of tools matching their domain.
"""

import json
from shopify_actions import ShopifyActions


# ── Tool Schemas ──────────────────────────────────────────────────────────────

BLAZE_TOOLS = [
    {
        "name": "create_flash_sale",
        "description": (
            "Create a real Shopify discount code for a flash sale. "
            "This immediately creates a working promo code customers can use at checkout."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string",  "description": "Flash sale name (e.g. 'Monday Madness')"},
                "discount_percent": {"type": "number",  "description": "Discount percentage, e.g. 20 for 20% off"},
                "duration_hours":   {"type": "integer", "description": "How many hours the sale runs"},
                "usage_limit":      {"type": "integer", "description": "Max number of redemptions (omit for unlimited)"},
                "code":             {"type": "string",  "description": "Custom promo code (omit to auto-generate)"},
            },
            "required": ["title", "discount_percent", "duration_hours"],
        },
    },
    {
        "name": "get_active_promotions",
        "description": "List all currently active discount codes and price rules on the store.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

PRISM_TOOLS = [
    {
        "name": "get_products_with_prices",
        "description": "Get all products with their current prices and inventory levels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max products to return (default 50)"},
            },
        },
    },
    {
        "name": "update_product_price",
        "description": (
            "Update a product variant's price on Shopify. "
            "Set compare_at_price to the original price to show a strikethrough 'was' price."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "variant_id":       {"type": "integer", "description": "Shopify variant ID"},
                "new_price":        {"type": "number",  "description": "New price in dollars"},
                "compare_at_price": {"type": "number",  "description": "Original price to show as strikethrough (optional)"},
            },
            "required": ["variant_id", "new_price"],
        },
    },
]

HALO_TOOLS = [
    {
        "name": "get_abandoned_checkouts",
        "description": (
            "Get detailed list of abandoned checkouts including customer email, "
            "cart value, items, and recovery URLs."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "create_flash_sale",
        "description": "Create a recovery discount code to attach to abandoned cart emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string", "description": "Code name, e.g. 'Cart Recovery 10% Off'"},
                "discount_percent": {"type": "number", "description": "Discount percentage"},
                "duration_hours":   {"type": "integer","description": "Hours until code expires"},
                "usage_limit":      {"type": "integer","description": "Limit to one use per customer"},
                "code":             {"type": "string", "description": "Custom code like COMEBACK10"},
            },
            "required": ["title", "discount_percent", "duration_hours"],
        },
    },
]

LUNA_TOOLS = [
    {
        "name": "create_product_listing",
        "description": (
            "Create a real, live product listing on the Shopify store. "
            "The product goes live immediately and is available for purchase. "
            "Use this to launch new products as part of the passive income strategy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":            {"type": "string",  "description": "SEO-optimised product title (under 60 chars)"},
                "description":      {"type": "string",  "description": "HTML product description with <p> and <ul> tags"},
                "price":            {"type": "number",  "description": "Retail price in USD, e.g. 29.99"},
                "compare_at_price": {"type": "number",  "description": "Original price for strikethrough display (optional)"},
                "product_type":     {"type": "string",  "description": "Category, e.g. 'Apparel', 'Home Decor', 'Kitchen'"},
                "tags":             {"type": "array",   "items": {"type": "string"}, "description": "List of tags for search and filtering"},
                "sku":              {"type": "string",  "description": "Stock keeping unit code (optional, auto-generated if omitted)"},
            },
            "required": ["title", "description", "price"],
        },
    },
    {
        "name": "get_store_collections",
        "description": "List all product collections in the Shopify store for categorisation.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_products_with_prices",
        "description": "Get the current product catalog to avoid duplicates and understand what's already listed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max products to return (default 50)"},
            },
        },
    },
]

CIPHER_TOOLS = [
    {
        "name": "get_revenue_by_day",
        "description": (
            "Get daily revenue breakdown for the last N days. "
            "Use this to spot trends, identify best/worst days, and calculate growth rate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days to look back (default 30, max 90)"},
            },
        },
    },
    {
        "name": "get_top_products_by_revenue",
        "description": (
            "Get the top products ranked by revenue over the last N days. "
            "Use this to identify winners to promote and losers to cut or reprice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days":  {"type": "integer", "description": "Lookback period in days (default 30)"},
                "limit": {"type": "integer", "description": "Number of top products to return (default 10)"},
            },
        },
    },
    {
        "name": "get_conversion_funnel",
        "description": (
            "Get conversion funnel metrics: completed orders vs abandoned carts, "
            "conversion rate, and the dollar value sitting in abandoned carts right now."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_channel_snapshot",
        "description": (
            "Get a full store health snapshot: revenue (7d and 30d), order counts, "
            "AOV, customer counts, and estimated repeat rate. "
            "Use this as the starting point for any analytics report."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_products_with_prices",
        "description": "Get the full product catalog with prices and inventory levels.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max products to return (default 50)"},
            },
        },
    },
]

TOOLS_BY_AGENT = {
    "BLAZE":  BLAZE_TOOLS,
    "PRISM":  PRISM_TOOLS,
    "HALO":   HALO_TOOLS,
    "LUNA":   LUNA_TOOLS,
    "CIPHER": CIPHER_TOOLS,
}


# ── Tool Runner ───────────────────────────────────────────────────────────────

class ToolRunner:
    """Executes tool calls from agents against the real Shopify store."""

    def __init__(self):
        self.actions = ShopifyActions()

    def execute(self, tool_name: str, tool_input: dict) -> str:
        """Dispatch a tool call and return a JSON string result."""
        try:
            result = self._dispatch(tool_name, tool_input)
            return json.dumps(result, indent=2)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "Forbidden" in error_msg:
                return json.dumps({
                    "error": "Permission denied",
                    "detail": (
                        f"Your Shopify app is missing the required write scope for '{tool_name}'. "
                        "Go to Shopify Admin → Settings → Apps → your app → Configure API scopes "
                        "and add the required write permissions, then reinstall the app."
                    )
                })
            if "401" in error_msg or "Unauthorized" in error_msg:
                return json.dumps({
                    "error": "Unauthorized",
                    "detail": "Invalid or expired Shopify access token. Check SHOPIFY_ACCESS_TOKEN in .env"
                })
            return json.dumps({"error": str(e)})

    def _dispatch(self, tool_name: str, inputs: dict) -> dict:
        if tool_name == "create_flash_sale":
            return self.actions.create_flash_sale(
                title=inputs["title"],
                discount_percent=inputs["discount_percent"],
                duration_hours=inputs.get("duration_hours", 6),
                usage_limit=inputs.get("usage_limit"),
                code=inputs.get("code"),
            )
        if tool_name == "get_active_promotions":
            rules = self.actions.get_active_discount_codes()
            return {"active_promotions": rules, "count": len(rules)}

        if tool_name == "get_products_with_prices":
            products = self.actions.get_products_with_prices(
                limit=inputs.get("limit", 50)
            )
            return {"products": products, "count": len(products)}
        if tool_name == "update_product_price":
            return self.actions.update_product_price(
                variant_id=inputs["variant_id"],
                new_price=inputs["new_price"],
                compare_at_price=inputs.get("compare_at_price"),
            )

        if tool_name == "get_abandoned_checkouts":
            checkouts = self.actions.get_abandoned_checkout_details()
            total_value = sum(c["total_price"] for c in checkouts)
            return {
                "abandoned_checkouts": checkouts,
                "count": len(checkouts),
                "total_recoverable_value": round(total_value, 2),
            }

        if tool_name == "create_product_listing":
            tags = inputs.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            return self.actions.create_product(
                title=inputs["title"],
                description=inputs["description"],
                price=inputs["price"],
                product_type=inputs.get("product_type", ""),
                tags=tags,
                compare_at_price=inputs.get("compare_at_price"),
                sku=inputs.get("sku"),
            )

        if tool_name == "get_store_collections":
            return {"collections": self.actions.get_collections()}

        if tool_name == "get_revenue_by_day":
            return self.actions.get_revenue_by_day(days=min(inputs.get("days", 30), 90))

        if tool_name == "get_top_products_by_revenue":
            return {
                "top_products": self.actions.get_top_products_by_revenue(
                    days=inputs.get("days", 30),
                    limit=inputs.get("limit", 10),
                )
            }

        if tool_name == "get_conversion_funnel":
            return self.actions.get_conversion_funnel()

        if tool_name == "get_channel_snapshot":
            return self.actions.get_channel_snapshot()

        return {"error": f"Unknown tool: {tool_name}"}
