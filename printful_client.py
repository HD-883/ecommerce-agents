"""
Printful print-on-demand integration.
When configured, agents can create products that Printful fulfills automatically —
no inventory, no warehouse. Orders sync from Shopify and Printful ships them.
"""

import os
import requests


# Popular Printful catalog IDs for quick product creation
PRINTFUL_CATALOG = {
    "unisex_tshirt":      {"id": 71,  "name": "Unisex Staple T-Shirt",       "base_cost": 12.95, "apparel": True},
    "premium_tshirt":     {"id": 145, "name": "Unisex Heavy Cotton Tee",      "base_cost": 13.25, "apparel": True},
    "hoodie":             {"id": 380, "name": "Unisex Heavy Blend Hoodie",    "base_cost": 27.95, "apparel": True},
    "mug_11oz":           {"id": 19,  "name": "White Glossy Mug 11oz",        "base_cost": 8.95,  "apparel": False},
    "mug_15oz":           {"id": 84,  "name": "White Glossy Mug 15oz",        "base_cost": 9.95,  "apparel": False},
    "tote_bag":           {"id": 523, "name": "Tote Bag",                     "base_cost": 9.95,  "apparel": False},
    "phone_case_iphone":  {"id": 266, "name": "iPhone Tough Case",           "base_cost": 14.95, "apparel": False},
    "poster_12x16":       {"id": 1,   "name": "Enhanced Matte Paper Poster", "base_cost": 11.95, "apparel": False},
    "canvas_16x20":       {"id": 3,   "name": "Canvas",                      "base_cost": 29.95, "apparel": False},
    "embroidered_hat":    {"id": 74,  "name": "Classic Dad Hat",              "base_cost": 18.95, "apparel": True},
    "notebook":           {"id": 505, "name": "Spiral Notebook",              "base_cost": 12.95, "apparel": False},
    "sticker_sheet":      {"id": 358, "name": "Kiss-Cut Sticker Sheet",       "base_cost": 4.25,  "apparel": False},
}

SUGGESTED_MARGINS = {
    "unisex_tshirt":      2.8,
    "premium_tshirt":     2.8,
    "hoodie":             2.5,
    "mug_11oz":           3.5,
    "mug_15oz":           3.2,
    "tote_bag":           3.0,
    "phone_case_iphone":  2.6,
    "poster_12x16":       3.0,
    "canvas_16x20":       2.4,
    "embroidered_hat":    2.6,
    "notebook":           2.8,
    "sticker_sheet":      4.0,
}


class PrintfulClient:
    BASE_URL = "https://api.printful.com"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("PRINTFUL_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in ("", "your_printful_key_here"))

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _get(self, endpoint: str, params: dict = None) -> dict:
        resp = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            headers=self._headers(),
            params=params or {},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, endpoint: str, payload: dict) -> dict:
        resp = requests.post(
            f"{self.BASE_URL}/{endpoint}",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_store_info(self) -> dict:
        """Verify connection and get store details."""
        return self._get("stores")

    def get_catalog_product(self, product_id: int) -> dict:
        """Get details for a catalog product including available variants."""
        return self._get(f"products/{product_id}")

    def get_catalog_variants(self, product_id: int) -> list:
        """Get all variants (sizes, colors) for a catalog product."""
        data = self._get(f"products/{product_id}")
        return data.get("result", {}).get("variants", [])

    def create_sync_product(
        self,
        name: str,
        description: str,
        catalog_product_key: str,
        print_file_url: str,
        retail_price: float,
        colors: list[str] = None,
        sizes: list[str] = None,
    ) -> dict:
        """
        Create a Printful sync product linked to Shopify.
        Printful will handle fulfillment when orders come in.
        """
        if catalog_product_key not in PRINTFUL_CATALOG:
            raise ValueError(f"Unknown catalog product: {catalog_product_key}. "
                           f"Options: {list(PRINTFUL_CATALOG.keys())}")

        catalog = PRINTFUL_CATALOG[catalog_product_key]
        variants_data = self.get_catalog_variants(catalog["id"])

        if not variants_data:
            raise ValueError(f"No variants returned from Printful for {catalog_product_key} "
                             f"(id {catalog['id']}). The catalog ID may have changed.")

        is_apparel = catalog.get("apparel", False)

        if is_apparel:
            wanted_colors = set(c.upper() for c in (colors or ["White", "Black", "Navy"]))
            wanted_sizes  = set(s.upper() for s in (sizes  or ["S", "M", "L", "XL"]))
            sync_variants = []
            for v in variants_data:
                color = (v.get("color") or "").upper()
                size  = (v.get("size")  or "").upper()
                if color in wanted_colors and size in wanted_sizes:
                    sync_variants.append({
                        "retail_price": str(retail_price),
                        "variant_id": v["id"],
                        "files": [{"url": print_file_url}],
                    })
                    if len(sync_variants) >= 12:
                        break
            # Fallback: first 3 variants if color/size filter matched nothing
            if not sync_variants:
                sync_variants = [
                    {"retail_price": str(retail_price), "variant_id": v["id"], "files": [{"url": print_file_url}]}
                    for v in variants_data[:3]
                ]
        else:
            # Non-apparel (mugs, posters, totes, canvas, notebooks):
            # take all variants as-is — they don't use clothing color/size nomenclature
            sync_variants = [
                {"retail_price": str(retail_price), "variant_id": v["id"], "files": [{"url": print_file_url}]}
                for v in variants_data[:6]
            ]

        payload = {
            "sync_product": {
                "name": name,
                "description": description,
            },
            "sync_variants": sync_variants,
        }
        return self._post("store/products", payload)

    def list_sync_products(self) -> list:
        """List all products synced to Printful."""
        data = self._get("store/products", {"limit": 100})
        return data.get("result", {}).get("result", [])

    def get_shipping_estimate(self, country_code: str = "US") -> dict:
        """Rough shipping cost estimate for a country."""
        estimates = {
            "US": {"standard": 3.99, "express": 9.99},
            "CA": {"standard": 6.99, "express": 14.99},
            "GB": {"standard": 7.99, "express": 16.99},
            "AU": {"standard": 8.99, "express": 19.99},
        }
        return estimates.get(country_code, {"standard": 9.99, "express": 19.99})

    @staticmethod
    def suggested_retail_price(catalog_key: str, margin_multiplier: float = None) -> float:
        """Calculate a retail price given the base cost and desired margin."""
        if catalog_key not in PRINTFUL_CATALOG:
            return 29.99
        base  = PRINTFUL_CATALOG[catalog_key]["base_cost"]
        multi = margin_multiplier or SUGGESTED_MARGINS.get(catalog_key, 2.5)
        raw   = base * multi
        return round(raw - 0.01, 2)

    @staticmethod
    def catalog_summary() -> str:
        """Human-readable summary of available print-on-demand products."""
        lines = ["Available Printful Print-on-Demand Products:\n"]
        for key, info in PRINTFUL_CATALOG.items():
            suggested = PrintfulClient.suggested_retail_price(key)
            profit    = suggested - info["base_cost"]
            margin    = (profit / suggested) * 100
            lines.append(
                f"  {key:22s} | Base: ${info['base_cost']:5.2f} | "
                f"Suggested retail: ${suggested:6.2f} | "
                f"Profit/unit: ${profit:.2f} ({margin:.0f}%)"
            )
        return "\n".join(lines)
