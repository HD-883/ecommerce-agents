"""
Pexels image search — finds matching product photos for Shopify listings.
Free tier: 200 requests/hour, 20,000/month. No attribution required via API.
"""

import os
import re
import requests


class ImageFinder:
    PEXELS_URL = "https://api.pexels.com/v1/search"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("PEXELS_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in ("", "your_pexels_key_here"))

    def search(self, query: str, count: int = 3, orientation: str = "landscape") -> list[str]:
        """
        Search Pexels for photos matching the query.
        Returns a list of image URLs (large format, ~1200px wide).
        """
        if not self.is_configured():
            return []

        try:
            resp = requests.get(
                self.PEXELS_URL,
                headers={"Authorization": self.api_key},
                params={
                    "query":       query,
                    "per_page":    count + 3,   # fetch a few extras, pick the best
                    "orientation": orientation,
                },
                timeout=10,
            )
            resp.raise_for_status()
            photos = resp.json().get("photos", [])
            return [p["src"]["large"] for p in photos[:count]]
        except Exception:
            return []

    def find_for_product(
        self,
        product_name: str,
        product_type: str = "",
        tagline: str = "",
        count: int = 3,
    ) -> list[str]:
        """
        Find matching images for a product using progressive keyword fallback.
        Tries specific → broader → category until we get results.
        """
        # Build search queries from most to least specific
        queries = self._build_queries(product_name, product_type, tagline)

        for query in queries:
            urls = self.search(query, count=count)
            if urls:
                return urls

        return []

    def _build_queries(self, name: str, product_type: str, tagline: str) -> list[str]:
        """Generate a ranked list of search queries from specific to broad."""
        queries = []

        # 1. Clean product name as primary query
        clean_name = re.sub(r"[^\w\s]", "", name).strip()
        if clean_name:
            queries.append(clean_name)

        # 2. Name + type combo
        if product_type:
            queries.append(f"{clean_name} {product_type}".strip())

        # 3. Key words from tagline
        if tagline:
            # Extract meaningful words (skip filler)
            stopwords = {"the", "a", "an", "is", "for", "with", "your", "our", "that", "this"}
            words = [w for w in tagline.lower().split() if w not in stopwords and len(w) > 3]
            if words:
                queries.append(" ".join(words[:4]))

        # 4. Product type alone as fallback
        if product_type:
            queries.append(product_type)

        # 5. Generic lifestyle fallback
        queries.append("product lifestyle minimal")

        return queries


# ── Convenience function ──────────────────────────────────────────────────────

def get_product_images(
    product_name: str,
    product_type: str = "",
    tagline: str = "",
    count: int = 3,
    api_key: str = None,
) -> list[str]:
    """Top-level helper used by the pipeline."""
    finder = ImageFinder(api_key=api_key)
    return finder.find_for_product(product_name, product_type, tagline, count)
