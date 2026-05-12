"""
22 Real-Time Income Generation Ideas for Legacy Commerce Inc.
Each idea includes metadata for AI evaluation by the agent team.
"""

INCOME_IDEAS = [
    {
        "id": "01",
        "name": "Live Shopping Events",
        "description": (
            "Host real-time product demos and flash sales on TikTok Live, Instagram Live, "
            "and YouTube Live Commerce. Products sell directly during the stream with "
            "comment-triggered checkout links and limited-quantity countdown timers."
        ),
        "category": "Content & Sales",
        "investment_level": "Medium",
        "time_to_revenue": "1–2 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 7,
        "primary_owner": "SPARK",
        "supporting_agents": ["TEMPO", "LUNA", "BLAZE"],
    },
    {
        "id": "02",
        "name": "Automated Flash Sale Engine",
        "description": (
            "Trigger time-limited sales (2–6 hours) automatically based on inventory levels, "
            "day of week, and sales velocity. Countdown timers, scarcity badges, and push "
            "notifications fire simultaneously across all channels."
        ),
        "category": "Sales Automation",
        "investment_level": "Low",
        "time_to_revenue": "3–5 days",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 9,
        "primary_owner": "BLAZE",
        "supporting_agents": ["PRISM", "HALO", "ZARA"],
    },
    {
        "id": "03",
        "name": "AI Dynamic Pricing",
        "description": (
            "Real-time price optimization engine that adjusts prices based on demand signals, "
            "competitor pricing, time of day, inventory remaining, and customer segment. "
            "Integrates directly with Shopify via Prisync or Wiser."
        ),
        "category": "Revenue Optimization",
        "investment_level": "Medium",
        "time_to_revenue": "2–3 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 6,
        "primary_owner": "PRISM",
        "supporting_agents": ["CIPHER", "ZARA"],
    },
    {
        "id": "04",
        "name": "Abandoned Cart Recovery (Multi-Channel)",
        "description": (
            "Automated 3-step recovery: Email at 1hr → SMS at 4hr → Push notification at 24hr. "
            "Each step has personalized content, urgency element, and optional discount escalation. "
            "Proven 15–25% cart recovery rate with proper sequencing."
        ),
        "category": "Automation",
        "investment_level": "Low",
        "time_to_revenue": "1 week",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 9,
        "primary_owner": "HALO",
        "supporting_agents": ["BLAZE", "ZARA", "FELIX"],
    },
    {
        "id": "05",
        "name": "Subscription Box Program",
        "description": (
            "Monthly curated product boxes with auto-renewing subscriptions. Options: "
            "themed boxes (seasonal), mystery boxes (surprise), or build-your-own. "
            "Shopify Subscriptions app or Recharge handles billing. Creates predictable MRR."
        ),
        "category": "Recurring Revenue",
        "investment_level": "Medium",
        "time_to_revenue": "3–4 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 6,
        "primary_owner": "REX",
        "supporting_agents": ["LUNA", "HALO", "FELIX"],
    },
    {
        "id": "06",
        "name": "Digital Products & Instant Downloads",
        "description": (
            "Create and sell digital goods: how-to guides, home décor inspiration packs, "
            "DIY templates, care instruction PDFs, style lookbooks. Instant delivery, "
            "100% margin after creation, infinitely scalable."
        ),
        "category": "High-Margin Revenue",
        "investment_level": "Low",
        "time_to_revenue": "1–2 weeks",
        "revenue_potential": "Medium-High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 8,
        "primary_owner": "ECHO",
        "supporting_agents": ["LUNA", "TEMPO"],
    },
    {
        "id": "07",
        "name": "24/7 AI Sales Chatbot",
        "description": (
            "Deploy conversational AI chatbot on site to qualify visitors, recommend products "
            "based on needs, handle FAQs, and push hesitant shoppers to checkout. "
            "Integrates with Shopify product catalog and customer history."
        ),
        "category": "Conversion Automation",
        "investment_level": "Medium",
        "time_to_revenue": "2 weeks",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 7,
        "primary_owner": "JADE",
        "supporting_agents": ["ZARA", "CIPHER"],
    },
    {
        "id": "08",
        "name": "B2B Wholesale Portal",
        "description": (
            "Dedicated wholesale channel for interior designers, gift shops, and bulk buyers. "
            "Tiered pricing (MOQ-based), net-30 payment terms, custom ordering portal. "
            "Shopify B2B or Handshake integration. AOV is typically 5–20x retail."
        ),
        "category": "New Revenue Channel",
        "investment_level": "Medium",
        "time_to_revenue": "3–4 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 5,
        "primary_owner": "ZARA",
        "supporting_agents": ["REX", "NOVA", "CIPHER"],
    },
    {
        "id": "09",
        "name": "Affiliate & Influencer Program",
        "description": (
            "Launch commission-based program (10–20%) for bloggers, content creators, and "
            "micro-influencers. Use Shopify Collabs or Refersion for tracking. "
            "Leverage our 50-year brand story as a content angle."
        ),
        "category": "Performance Marketing",
        "investment_level": "Low",
        "time_to_revenue": "2–3 weeks",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 7,
        "primary_owner": "TEMPO",
        "supporting_agents": ["LUNA", "CIPHER"],
    },
    {
        "id": "10",
        "name": "AI-Powered Product Bundling",
        "description": (
            "Real-time 'Frequently Bought Together' and 'Complete the Look' recommendations "
            "powered by purchase history data. Increases AOV by 20–35%. "
            "Built into Shopify checkout or via Bold Bundles app."
        ),
        "category": "Revenue Optimization",
        "investment_level": "Low",
        "time_to_revenue": "1 week",
        "revenue_potential": "Medium-High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 9,
        "primary_owner": "PRISM",
        "supporting_agents": ["CIPHER", "ZARA"],
    },
    {
        "id": "11",
        "name": "Browser & Mobile Push Notifications",
        "description": (
            "One-click opt-in push notification system for flash deals, back-in-stock alerts, "
            "and personalized offers. No email address required. "
            "PushOwl or OneSignal integrates natively with Shopify."
        ),
        "category": "Retention Marketing",
        "investment_level": "Low",
        "time_to_revenue": "3–5 days",
        "revenue_potential": "Medium-High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 8,
        "primary_owner": "BLAZE",
        "supporting_agents": ["HALO", "CIPHER"],
    },
    {
        "id": "12",
        "name": "TikTok Shop & Instagram Shopping",
        "description": (
            "Native in-app shopping with zero-redirect checkout on TikTok Shop and Instagram. "
            "Products tagged directly in videos, Reels, and Stories. "
            "Shopify syncs catalog automatically. Algorithm-driven discovery brings new buyers."
        ),
        "category": "New Sales Channel",
        "investment_level": "Low",
        "time_to_revenue": "1–2 weeks",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 7,
        "primary_owner": "TEMPO",
        "supporting_agents": ["SPARK", "LUNA", "ECHO"],
    },
    {
        "id": "13",
        "name": "Real-Time Loyalty Cashback Program",
        "description": (
            "Instant cashback rewards credited at checkout — e.g., earn 5% back on every "
            "purchase, redeemable immediately on the next order. "
            "Creates addiction loop: spend → earn → redeem → spend more."
        ),
        "category": "Retention & Loyalty",
        "investment_level": "Medium",
        "time_to_revenue": "2–3 weeks",
        "revenue_potential": "Medium (drives 3x repeat purchase rate)",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 6,
        "primary_owner": "FELIX",
        "supporting_agents": ["ZARA", "CIPHER"],
    },
    {
        "id": "14",
        "name": "Pre-Order Campaigns",
        "description": (
            "Collect payment before inventory arrives for new or seasonal products. "
            "Gauges real demand, funds inventory procurement, and creates anticipation. "
            "Best for limited editions, seasonal items, and new product launches."
        ),
        "category": "Cash Flow Optimization",
        "investment_level": "Low",
        "time_to_revenue": "Immediate",
        "revenue_potential": "Medium-High",
        "recurring": False,
        "shopify_compatible": True,
        "convenience_score": 7,
        "primary_owner": "ZARA",
        "supporting_agents": ["REX", "BLAZE", "HALO"],
    },
    {
        "id": "15",
        "name": "Marketplace Expansion (Amazon/eBay/Etsy)",
        "description": (
            "Sync Shopify catalog to Amazon, eBay, and Etsy via LitCommerce or Sellbrite. "
            "Immediate access to 350M+ combined buyers. Leverage our 50-year reputation "
            "and existing product catalog — minimal new content required."
        ),
        "category": "Channel Expansion",
        "investment_level": "Medium",
        "time_to_revenue": "2–4 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 6,
        "primary_owner": "REX",
        "supporting_agents": ["PRISM", "VEIL", "NOVA"],
    },
    {
        "id": "16",
        "name": "Buy Now Pay Later (BNPL)",
        "description": (
            "Add Afterpay, Klarna, or Affirm at checkout. Proven to increase conversion "
            "rate by 20–30% and AOV by 40%+ for orders over $100. "
            "Native Shopify integration — live in under 48 hours."
        ),
        "category": "Conversion Optimization",
        "investment_level": "Low",
        "time_to_revenue": "48 hours",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 10,
        "primary_owner": "ZARA",
        "supporting_agents": ["VEIL", "PRISM"],
    },
    {
        "id": "17",
        "name": "AI Personalization Engine",
        "description": (
            "Real-time personalized homepage, product feeds, and email content per visitor "
            "based on browse history, purchase data, and behavioral signals. "
            "Tools: Nosto, LimeSpot, or Shopify's native recommendations."
        ),
        "category": "Conversion Optimization",
        "investment_level": "High",
        "time_to_revenue": "4–6 weeks",
        "revenue_potential": "Very High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 5,
        "primary_owner": "CIPHER",
        "supporting_agents": ["PRISM", "HALO", "ECHO"],
    },
    {
        "id": "18",
        "name": "SMS VIP Flash Deal List",
        "description": (
            "Build an exclusive SMS list of top 500 customers. Send VIP-only flash deals "
            "24 hours before public launch. 98% open rate. Creates elite customer status "
            "and drives highest-LTV segment to purchase first."
        ),
        "category": "Retention Marketing",
        "investment_level": "Low",
        "time_to_revenue": "1 week",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 8,
        "primary_owner": "HALO",
        "supporting_agents": ["BLAZE", "FELIX", "CIPHER"],
    },
    {
        "id": "19",
        "name": "Limited Edition Product Drops",
        "description": (
            "Quarterly limited-quantity product releases with built-up anticipation marketing: "
            "teaser content 2 weeks before, waitlist signup, drop-day countdown. "
            "Creates brand excitement, premium pricing justification, and sellout events."
        ),
        "category": "Brand & Sales Strategy",
        "investment_level": "Medium",
        "time_to_revenue": "Immediate (on drop day)",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 6,
        "primary_owner": "BLAZE",
        "supporting_agents": ["LUNA", "TEMPO", "REX"],
    },
    {
        "id": "20",
        "name": "Customer Referral Program",
        "description": (
            "Mutual reward referral system: existing customer gets $15 store credit, "
            "new customer gets $10 off first order. Automated via ReferralCandy or "
            "Shopify Flow. Lowest CAC channel — trust-based acquisition."
        ),
        "category": "Acquisition & Retention",
        "investment_level": "Low",
        "time_to_revenue": "2–3 weeks",
        "revenue_potential": "High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 8,
        "primary_owner": "FELIX",
        "supporting_agents": ["ZARA", "HALO", "CIPHER"],
    },
    {
        "id": "21",
        "name": "Post-Purchase Upsell (One-Click)",
        "description": (
            "Display a single irresistible upsell offer on the order confirmation page — "
            "one click, no re-entering payment info. Avg. 10–15% acceptance rate adds "
            "direct margin. ReConvert app integrates natively with Shopify checkout."
        ),
        "category": "Revenue Optimization",
        "investment_level": "Low",
        "time_to_revenue": "1–3 days",
        "revenue_potential": "Medium-High",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 10,
        "primary_owner": "PRISM",
        "supporting_agents": ["ZARA", "CIPHER"],
    },
    {
        "id": "22",
        "name": "Back-in-Stock & Price Drop Alerts",
        "description": (
            "Automated alerts when a wishlisted item restocks or drops in price. "
            "Captures demand that would otherwise be lost. Converts high-intent "
            "window shoppers into buyers at the exact right moment."
        ),
        "category": "Automation",
        "investment_level": "Low",
        "time_to_revenue": "3–5 days",
        "revenue_potential": "Medium",
        "recurring": True,
        "shopify_compatible": True,
        "convenience_score": 9,
        "primary_owner": "HALO",
        "supporting_agents": ["REX", "PRISM", "BLAZE"],
    },
]

# Quick lookup by id
IDEAS_BY_ID = {idea["id"]: idea for idea in INCOME_IDEAS}

# Top 10 by convenience score (quick wins)
QUICK_WINS = sorted(
    [i for i in INCOME_IDEAS if i["investment_level"] == "Low"],
    key=lambda x: x["convenience_score"],
    reverse=True,
)[:10]

# Ideas by category
IDEAS_BY_CATEGORY = {}
for idea in INCOME_IDEAS:
    cat = idea["category"]
    IDEAS_BY_CATEGORY.setdefault(cat, []).append(idea)
