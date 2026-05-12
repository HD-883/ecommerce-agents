"""
Passive Income Pipeline — agents autonomously create, list, and market products.

Flow:
  1. ARIA picks a niche and sets the strategy
  2. LUNA generates product concepts (name, hook, target buyer)
  3. ECHO writes SEO-optimised titles and descriptions
  4. PRISM sets retail prices with margin targets
  5. Products get created live in Shopify via API
  6. TEMPO writes social launch posts
  7. HALO writes the launch email
  8. Telegram notification with a full summary
"""

import json
import re
import os
from dataclasses import dataclass, field
from datetime import datetime

import anthropic
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from config import AGENT_CONFIGS, BUSINESS_CONTEXT
from agents import AgentFactory
from shopify_actions import ShopifyActions
from printful_client import PrintfulClient, PRINTFUL_CATALOG, PrintfulClient as PC
from telegram_notify import TelegramNotifier

console = Console()


@dataclass
class ProductConcept:
    name: str = ""
    tagline: str = ""
    target_buyer: str = ""
    product_type: str = ""
    key_benefit: str = ""
    printful_key: str = ""
    price: float = 0.0
    compare_at: float = 0.0
    tags: list[str] = field(default_factory=list)
    seo_title: str = ""
    seo_description: str = ""
    social_post: str = ""
    shopify_result: dict = field(default_factory=dict)


class PassiveIncomePipeline:
    """
    Full autonomous pipeline: niche → ideas → listings → Shopify → marketing.
    Each stage is handled by the specialist agent for that domain.
    """

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.agents  = AgentFactory.create_all(self.client)
        self.shopify = ShopifyActions()
        self.printful = PrintfulClient()
        self.telegram = TelegramNotifier()
        self._started = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ─────────────────────────────────────────────────────────────────────────

    def run(
        self,
        niche: str = None,
        count: int = 5,
        use_printful: bool = False,
        dry_run: bool = False,
    ) -> list[ProductConcept]:
        """
        Run the full passive income pipeline.
        dry_run=True generates all content but skips the Shopify API calls.
        """
        console.print(
            Panel(
                "[bold yellow]PASSIVE INCOME PIPELINE[/bold yellow]\n"
                "[white]Agents will research, create, list, and market real products[/white]\n"
                f"[dim]Target: {count} products · "
                f"{'Printful POD' if use_printful else 'Shopify listings'} · "
                f"{'DRY RUN' if dry_run else 'LIVE'}[/dim]",
                border_style="yellow",
                padding=(1, 4),
            )
        )

        # Stage 1 — strategy
        niche = self._stage_strategy(niche)

        # Stage 2 — product ideas
        concepts = self._stage_ideation(niche, count, use_printful)

        # Stage 3 — SEO content
        concepts = self._stage_seo(concepts)

        # Stage 4 — pricing
        concepts = self._stage_pricing(concepts, use_printful)

        # Stage 5 — create in Shopify
        if not dry_run:
            concepts = self._stage_create_listings(concepts)
        else:
            console.print("[yellow]⚠ DRY RUN — skipping Shopify product creation[/yellow]\n")

        # Stage 6 — marketing content
        concepts = self._stage_marketing(concepts)

        # Stage 7 — summary
        self._stage_summary(concepts, niche, dry_run)

        return concepts

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 1 — ARIA SETS THE STRATEGY
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_strategy(self, niche: str | None) -> str:
        aria = self.agents["ARIA"]
        console.print(Rule("[bold yellow]STAGE 1 — ARIA: NICHE STRATEGY[/bold yellow]"))

        if niche:
            prompt = (
                f"We're launching a passive income product line in the '{niche}' niche. "
                "As CRO, give a 3-sentence strategic rationale: why this niche fits our brand, "
                "what the opportunity size is, and the #1 pricing or positioning rule for success. "
                "Be direct and data-aware."
            )
        else:
            prompt = (
                "We're launching a passive income product line. As CRO, pick the single best niche "
                "for Legacy Commerce right now — given our home goods / lifestyle brand, 45K customers, "
                "and print-on-demand capabilities. Name the niche, explain why in 2 sentences, "
                "and state the exact product category. Start your response with 'NICHE: [name]'."
            )

        strategy = aria.think(prompt, max_tokens=300)
        console.print(Panel(strategy, title="[cyan]👩‍💼 ARIA — Strategy[/cyan]", border_style="cyan"))

        if not niche:
            for line in strategy.splitlines():
                if line.strip().upper().startswith("NICHE:"):
                    niche = line.split(":", 1)[-1].strip().strip('"').strip("'")
                    break
            if not niche:
                niche = "home & lifestyle"

        console.print(f"[bold green]✓ Niche locked: [white]{niche}[/white][/bold green]\n")
        return niche

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 2 — LUNA GENERATES PRODUCT IDEAS
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_ideation(self, niche: str, count: int, use_printful: bool) -> list[ProductConcept]:
        luna = self.agents["LUNA"]
        console.print(Rule("[bold yellow]STAGE 2 — LUNA: PRODUCT IDEATION[/bold yellow]"))

        printful_hint = ""
        if use_printful:
            printful_hint = (
                f"\n\nWe use Printful for fulfilment. Available product types: "
                f"{', '.join(PRINTFUL_CATALOG.keys())}. "
                f"For each idea also specify which printful_key to use."
            )

        prompt = (
            f"Create {count} distinct, sellable product ideas for the '{niche}' niche. "
            f"These will be listed on our Shopify store immediately and need to generate real revenue.\n"
            f"{printful_hint}\n\n"
            f"For each product return EXACTLY this JSON format (no extra text):\n"
            f"[\n"
            f'  {{\n'
            f'    "name": "Product Name",\n'
            f'    "tagline": "One punchy sentence hook",\n'
            f'    "target_buyer": "Exactly who buys this",\n'
            f'    "product_type": "Category (e.g. Apparel, Home Decor, Kitchen)",\n'
            f'    "key_benefit": "The #1 reason someone buys this",\n'
            f'    "printful_key": "mug_11oz"' + (' or empty string if not using Printful' if not use_printful else '') + '\n'
            f'  }}\n'
            f"]\n\n"
            f"Think commercial, specific, trend-aware. No generic products."
        )

        raw = luna.think(prompt, max_tokens=1200)

        concepts = []
        try:
            json_match = re.search(r'\[[\s\S]*\]', raw)
            if json_match:
                ideas = json.loads(json_match.group())
                for idea in ideas[:count]:
                    c = ProductConcept(
                        name=idea.get("name", ""),
                        tagline=idea.get("tagline", ""),
                        target_buyer=idea.get("target_buyer", ""),
                        product_type=idea.get("product_type", ""),
                        key_benefit=idea.get("key_benefit", ""),
                        printful_key=idea.get("printful_key", "") if use_printful else "",
                    )
                    concepts.append(c)
        except (json.JSONDecodeError, AttributeError):
            console.print("[yellow]⚠ Couldn't parse JSON — extracting ideas from text[/yellow]")
            concepts = self._parse_ideas_from_text(raw, count)

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#",           width=3,  style="dim")
        table.add_column("Product",     width=28, style="cyan")
        table.add_column("Type",        width=16, style="white")
        table.add_column("Target Buyer",width=28, style="dim")
        table.add_column("Key Benefit", width=32, style="green")

        for i, c in enumerate(concepts, 1):
            table.add_row(str(i), c.name, c.product_type, c.target_buyer, c.key_benefit)
        console.print(table)
        console.print()

        return concepts

    def _parse_ideas_from_text(self, text: str, count: int) -> list[ProductConcept]:
        """Fallback parser when the model returns text instead of JSON."""
        concepts = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        current = ProductConcept()
        for line in lines:
            if line.startswith('"name"') or ("name:" in line.lower() and len(concepts) < count):
                if current.name:
                    concepts.append(current)
                    current = ProductConcept()
                current.name = line.split(":", 1)[-1].strip().strip('",')
        if current.name:
            concepts.append(current)
        return concepts[:count]

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 3 — ECHO WRITES SEO CONTENT
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_seo(self, concepts: list[ProductConcept]) -> list[ProductConcept]:
        echo = self.agents["ECHO"]
        console.print(Rule("[bold yellow]STAGE 3 — ECHO: SEO TITLES & DESCRIPTIONS[/bold yellow]"))

        products_list = "\n".join(
            f"{i+1}. {c.name} — {c.tagline} | Buyer: {c.target_buyer} | Benefit: {c.key_benefit}"
            for i, c in enumerate(concepts)
        )

        prompt = (
            f"Write SEO-optimised product listings for these {len(concepts)} products.\n\n"
            f"{products_list}\n\n"
            f"Return EXACTLY this JSON (no extra text):\n"
            f"[\n"
            f'  {{\n'
            f'    "seo_title": "Under 60 chars, keyword-rich Shopify product title",\n'
            f'    "seo_description": "150-250 word HTML product description with <p> tags, ",'
            f'"bullet benefits in <ul><li>, and a closing CTA. No fluff."\n'
            f'  }}\n'
            f"]\n\n"
            f"Focus on search intent, conversion copy, and natural keyword placement. "
            f"Legacy Commerce is a trusted 50-year brand — use that credibility."
        )

        raw = echo.think(prompt, max_tokens=2500)

        try:
            json_match = re.search(r'\[[\s\S]*\]', raw)
            if json_match:
                seo_data = json.loads(json_match.group())
                for i, item in enumerate(seo_data):
                    if i < len(concepts):
                        concepts[i].seo_title = item.get("seo_title", concepts[i].name)
                        concepts[i].seo_description = item.get("seo_description", "")
        except (json.JSONDecodeError, AttributeError):
            console.print("[yellow]⚠ SEO JSON parse failed — using product names as titles[/yellow]")
            for c in concepts:
                if not c.seo_title:
                    c.seo_title = c.name

        console.print(f"[green]✓ SEO content written for {len(concepts)} products[/green]\n")
        return concepts

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 4 — PRISM SETS PRICING
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_pricing(self, concepts: list[ProductConcept], use_printful: bool) -> list[ProductConcept]:
        prism = self.agents["PRISM"]
        console.print(Rule("[bold yellow]STAGE 4 — PRISM: PRICING STRATEGY[/bold yellow]"))

        printful_costs = ""
        if use_printful:
            cost_lines = []
            for c in concepts:
                if c.printful_key and c.printful_key in PRINTFUL_CATALOG:
                    base = PRINTFUL_CATALOG[c.printful_key]["base_cost"]
                    suggested = PC.suggested_retail_price(c.printful_key)
                    cost_lines.append(f"  {c.name}: base cost ${base:.2f}, suggested ${suggested:.2f}")
            if cost_lines:
                printful_costs = "\n\nPrintful base costs (must cover these + 40%+ margin):\n" + "\n".join(cost_lines)

        products_list = "\n".join(
            f"{i+1}. {c.name} | Type: {c.product_type} | Buyer: {c.target_buyer}"
            for i, c in enumerate(concepts)
        )

        prompt = (
            f"Set retail prices for these {len(concepts)} products. "
            f"We target 40-60% gross margin. Use psychological pricing ($X.99 or $X.95). "
            f"Also set a compare_at_price (original price) for each to create a 'sale' effect — "
            f"set it 20-35% above the selling price.\n\n"
            f"{products_list}"
            f"{printful_costs}\n\n"
            f"Return EXACTLY this JSON:\n"
            f"[\n"
            f'  {{"price": 29.99, "compare_at": 39.99}}\n'
            f"]\n"
            f"One object per product, same order as the list. Numbers only, no strings."
        )

        raw = prism.think(prompt, max_tokens=600)

        try:
            json_match = re.search(r'\[[\s\S]*?\]', raw)
            if json_match:
                pricing = json.loads(json_match.group())
                for i, p in enumerate(pricing):
                    if i < len(concepts):
                        concepts[i].price = float(p.get("price", 29.99))
                        concepts[i].compare_at = float(p.get("compare_at", 0))
        except (json.JSONDecodeError, AttributeError):
            console.print("[yellow]⚠ Pricing JSON parse failed — using defaults[/yellow]")
            for c in concepts:
                if not c.price:
                    c.price = 29.99

        table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta")
        table.add_column("Product",         style="cyan", width=32)
        table.add_column("Price",           style="bold green", width=10)
        table.add_column("Compare At",      style="dim", width=12)
        table.add_column("Discount Shown",  style="yellow", width=14)

        for c in concepts:
            discount = ""
            if c.compare_at and c.compare_at > c.price:
                pct = int((1 - c.price / c.compare_at) * 100)
                discount = f"{pct}% off"
            table.add_row(c.name, f"${c.price:.2f}", f"${c.compare_at:.2f}" if c.compare_at else "—", discount)

        console.print(table)
        console.print()
        return concepts

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 5 — CREATE LISTINGS IN SHOPIFY
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_create_listings(self, concepts: list[ProductConcept]) -> list[ProductConcept]:
        console.print(Rule("[bold yellow]STAGE 5 — SHOPIFY: CREATING LIVE LISTINGS[/bold yellow]"))

        if not self.shopify.store_url or not self.shopify.access_token:
            console.print("[yellow]⚠ Shopify not configured — skipping listing creation.[/yellow]")
            console.print("[dim]Set SHOPIFY_STORE_URL and SHOPIFY_ACCESS_TOKEN in .env to go live.[/dim]\n")
            return concepts

        for i, c in enumerate(concepts):
            title = c.seo_title or c.name
            desc  = c.seo_description or f"<p>{c.tagline}</p><p>{c.key_benefit}</p>"
            tags  = c.tags or [c.product_type.lower(), "passive-income", "new-arrival"]

            console.print(f"  [dim]{i+1}/{len(concepts)}[/dim] Creating [cyan]{title}[/cyan]...", end=" ")
            try:
                result = self.shopify.create_product(
                    title=title,
                    description=desc,
                    price=c.price,
                    product_type=c.product_type,
                    tags=tags,
                    compare_at_price=c.compare_at if c.compare_at else None,
                )
                c.shopify_result = result
                console.print(f"[green]✓[/green] [dim]{result.get('shopify_url', '')}[/dim]")
            except Exception as e:
                c.shopify_result = {"error": str(e)}
                console.print(f"[red]✗ {e}[/red]")

        created  = sum(1 for c in concepts if c.shopify_result.get("success"))
        failed   = len(concepts) - created
        console.print(f"\n[bold green]✓ {created} products created live[/bold green]"
                      + (f"  [red]{failed} failed[/red]" if failed else "") + "\n")
        return concepts

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 6 — MARKETING CONTENT
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_marketing(self, concepts: list[ProductConcept]) -> list[ProductConcept]:
        tempo = self.agents["TEMPO"]
        halo  = self.agents["HALO"]
        console.print(Rule("[bold yellow]STAGE 6 — TEMPO & HALO: LAUNCH MARKETING[/bold yellow]"))

        product_list = "\n".join(
            f"- {c.name}: {c.tagline} (${c.price:.2f})"
            for c in concepts
        )

        # TEMPO — social media posts
        console.print("[bold]📱 TEMPO — Social Launch Posts[/bold]")
        social_prompt = (
            f"Write launch social posts for these new products:\n{product_list}\n\n"
            f"Create ONE Instagram caption AND one TikTok hook line for the collection launch. "
            f"Make them feel exciting, urgent, and authentic to a 50-year brand going digital. "
            f"Include relevant hashtags for the Instagram post. "
            f"Return as plain text with 'INSTAGRAM:' and 'TIKTOK:' labels."
        )
        social_content = tempo.think(social_prompt, max_tokens=400)
        console.print(Panel(social_content, title="[cyan]📱 TEMPO — Social Content[/cyan]", border_style="cyan"))

        # HALO — launch email
        console.print("\n[bold]✉️  HALO — Launch Email[/bold]")
        email_prompt = (
            f"Write a launch email for these {len(concepts)} new products:\n{product_list}\n\n"
            f"Format:\n"
            f"SUBJECT: [subject line under 50 chars]\n"
            f"PREVIEW: [preview text under 90 chars]\n"
            f"BODY: [3-paragraph email — opener with urgency, product highlights, CTA]\n\n"
            f"Legacy Commerce tone: trusted, warm, slightly nostalgic but modern. No emojis in the body."
        )
        email_content = halo.think(email_prompt, max_tokens=500)
        console.print(Panel(email_content, title="[cyan]✉️  HALO — Launch Email[/cyan]", border_style="cyan"))

        console.print()
        return concepts

    # ─────────────────────────────────────────────────────────────────────────
    # STAGE 7 — SUMMARY + TELEGRAM
    # ─────────────────────────────────────────────────────────────────────────

    def _stage_summary(self, concepts: list[ProductConcept], niche: str, dry_run: bool):
        console.print(Rule("[bold yellow]PIPELINE COMPLETE — REVENUE SUMMARY[/bold yellow]"))

        created   = [c for c in concepts if c.shopify_result.get("success")]
        total_rev = sum(c.price for c in concepts)
        avg_price = total_rev / len(concepts) if concepts else 0

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta", title="Products Created")
        table.add_column("Product",    style="cyan",       width=32)
        table.add_column("Price",      style="bold green", width=8)
        table.add_column("Compare At", style="dim",        width=10)
        table.add_column("Status",     style="white",      width=10)
        table.add_column("URL",        style="dim",        width=40)

        for c in concepts:
            status = "[green]LIVE[/green]" if c.shopify_result.get("success") else (
                "[yellow]DRY RUN[/yellow]" if dry_run else "[red]FAILED[/red]"
            )
            url = c.shopify_result.get("shopify_url", "—") if not dry_run else "—"
            table.add_row(
                c.name[:30],
                f"${c.price:.2f}",
                f"${c.compare_at:.2f}" if c.compare_at else "—",
                status,
                url,
            )
        console.print(table)

        console.print(
            f"\n[bold]Niche:[/bold] {niche}\n"
            f"[bold]Products:[/bold] {len(concepts)} generated · {len(created)} live\n"
            f"[bold]Avg price:[/bold] ${avg_price:.2f}\n"
            f"[bold]Potential revenue (if all sell 10x):[/bold] "
            f"[bold green]${total_rev * 10:,.2f}[/bold green]\n"
        )

        msg = self._telegram_summary(concepts, niche, dry_run)
        self.telegram.send(msg)

    def _telegram_summary(self, concepts: list[ProductConcept], niche: str, dry_run: bool) -> str:
        created = sum(1 for c in concepts if c.shopify_result.get("success"))
        lines = [
            f"🤖 *Passive Income Pipeline — {'DRY RUN' if dry_run else 'LIVE'}*",
            f"━━━━━━━━━━━━━━━━━",
            f"📦 Niche: *{niche}*",
            f"✅ Products created: *{created}/{len(concepts)}*",
            "",
        ]
        for c in concepts:
            url = c.shopify_result.get("shopify_url")
            status = "✅" if c.shopify_result.get("success") else ("🔄" if dry_run else "❌")
            line = f"{status} {c.name} — *${c.price:.2f}*"
            if url:
                line += f"\n   [View →]({url})"
            lines.append(line)

        lines += [
            "",
            f"[View store →](https://github.com/HD-883/ecommerce-agents/actions)",
        ]
        return "\n".join(lines)
