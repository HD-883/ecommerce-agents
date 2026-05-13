"""
Upload design images to ImgBB to get public URLs that Printful can download.
ImgBB is free (32 MB limit per image) and returns a permanent direct link.

Get a free API key at: https://api.imgbb.com/
Add it as IMGBB_API_KEY in GitHub Actions secrets.
"""

import base64
import os
import requests


IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


class DesignHosting:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("IMGBB_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key not in ("", "your_imgbb_key_here"))

    def upload(self, image_bytes: bytes, name: str = "design") -> str | None:
        """
        Upload raw PNG bytes to ImgBB and return the direct image URL.
        Returns None if upload fails or API key is not set.
        """
        if not self.is_configured():
            return None

        encoded = base64.b64encode(image_bytes).decode("utf-8")
        try:
            resp = requests.post(
                IMGBB_UPLOAD_URL,
                data={
                    "key": self.api_key,
                    "image": encoded,
                    "name": name[:50],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            # ImgBB returns data.data.url (display) or data.data.image.url (direct)
            url = (
                data.get("data", {}).get("image", {}).get("url")
                or data.get("data", {}).get("url")
            )
            return url
        except Exception:
            return None
