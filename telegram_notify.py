"""
Telegram notifications — sends agent summaries to your phone.
"""

import os
import requests


class TelegramNotifier:

    def __init__(self, token: str = None, chat_id: str = None):
        self.token   = token   or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id
                    and self.token not in ("", "your_token_here"))

    def send(self, text: str) -> bool:
        if not self.is_configured():
            return False
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id":    self.chat_id,
                    "text":       text,
                    "parse_mode": "Markdown",
                },
                timeout=10,
            )
            return True
        except Exception:
            return False

    # ── Pre-formatted message builders ───────────────────────────────────────

    def briefing_summary(self, snap: dict | None, directives_preview: str = "") -> str:
        if snap:
            inv_alerts = snap.get("out_of_stock_count", 0) + snap.get("low_stock_count", 0)
            inv_line   = f"⚠️ {inv_alerts} items low/out of stock" if inv_alerts else "✅ Stock levels healthy"
            body = (
                f"💰 Revenue today: *${snap['revenue_today']:,.2f}* ({snap['orders_today']} orders)\n"
                f"📦 Last 7 days:   *${snap['revenue_7d']:,.2f}* ({snap['orders_7d']} orders)\n"
                f"👥 New customers this week: {snap['new_customers_week']:,}\n"
                f"🛒 Abandoned carts: {snap['abandoned_count']} (${snap['abandoned_value']:,.2f})\n"
                f"{inv_line}"
            )
        else:
            body = "_No live Shopify data available_"

        return (
            f"🌅 *Morning Briefing — Legacy Commerce*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"{body}\n\n"
            f"[View full logs →](https://github.com/HD-883/ecommerce-agents/actions)"
        )

    def flash_sale_summary(self, result_text: str) -> str:
        # Try to extract the discount code from BLAZE's response
        code = "—"
        for line in result_text.splitlines():
            if "Code:" in line and "`" in line:
                code = line.split("`")[1] if "`" in line else line.split("Code:")[-1].strip()
                break
        return (
            f"⚡ *Flash Sale Launched — BLAZE*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"Discount code: `{code}`\n\n"
            f"[View full logs →](https://github.com/HD-883/ecommerce-agents/actions)"
        )

    def cart_recovery_summary(self, snap: dict | None) -> str:
        if snap:
            body = (
                f"🛒 Abandoned carts: *{snap['abandoned_count']}*\n"
                f"💵 Recoverable value: *${snap['abandoned_value']:,.2f}*"
            )
        else:
            body = "_No cart data available_"
        return (
            f"🛒 *Cart Recovery — HALO*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"{body}\n\n"
            f"[View full logs →](https://github.com/HD-883/ecommerce-agents/actions)"
        )

    def price_audit_summary(self) -> str:
        return (
            f"💎 *Price Audit Complete — PRISM*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"Pricing analysis done. Check logs for recommendations.\n\n"
            f"[View full logs →](https://github.com/HD-883/ecommerce-agents/actions)"
        )
