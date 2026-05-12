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

TOOLS_BY_AGENT = {
    "BLAZE": BLAZE_TOOLS,
    "PRISM": PRISM_TOOLS,
    "HALO":  HALO_TOOLS,
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

        return {"error": f"Unknown tool: {tool_name}"}
