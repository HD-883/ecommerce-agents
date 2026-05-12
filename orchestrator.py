"""
ARIA Orchestrator — Chief Revenue Officer Command Center
Manages all 15 agents, evaluates income strategies, and runs operations 24/7.
"""

import os
import anthropic
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule
from rich import box

from config import AGENT_CONFIGS, HIERARCHY, BUSINESS_CONTEXT
from agents import AgentFactory, BaseAgent
from income_ideas import INCOME_IDEAS, QUICK_WINS
from shopify_client import ShopifyClient
from agent_tools import TOOLS_BY_AGENT, ToolRunner
from telegram_notify import TelegramNotifier

console = Console()


class ARIAOrchestrator:
    """
    ARIA — Chief Revenue Officer of Legacy Commerce Inc.
    Primary command center for all 15 agents and revenue strategy.
    """

    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self.agents = AgentFactory.create_all(self.client)
        self.aria = self.agents["ARIA"]
        self.shopify = ShopifyClient()
        self.tool_runner = ToolRunner()
        self.telegram = TelegramNotifier()

    def _load_store_snapshot(self) -> tuple[dict | None, str]:
        """Try to pull live Shopify data. Returns (snapshot, context_string)."""
        if not self.shopify.is_configured():
            return None, ""
        try:
            snap = self.shopify.get_store_snapshot()
            if snap["errors"]:
                console.print(f"[yellow]⚠ Shopify partial errors: {', '.join(snap['errors'])}[/yellow]")
            ctx = self.shopify.format_briefing_context(snap)
            console.print("[green]✓ Live Shopify data loaded[/green]\n")
            return snap, ctx
        except Exception as e:
            console.print(f"[yellow]⚠ Could not load Shopify data: {e}[/yellow]\n")
            return None, ""

    # ─────────────────────────────────────────────────────────────────────────
    # DISPLAY HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _print_agent_header(self, agent: BaseAgent):
        console.print(
            Panel(
                f"[bold]{agent.emoji} {agent.name}[/bold]  ·  {agent.title}\n"
                f"[dim]{agent.level} · Reports to: {agent.reports_to}[/dim]",
                border_style="blue",
            )
        )

    def _print_response(self, agent: BaseAgent, text: str):
        console.print(
            Panel(
                text,
                title=f"[cyan]{agent.emoji} {agent.name}[/cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    def _section(self, title: str):
        console.print()
        console.print(Rule(f"[bold yellow]{title}[/bold yellow]"))
        console.print()

    # ─────────────────────────────────────────────────────────────────────────
    # HIERARCHY DISPLAY
    # ─────────────────────────────────────────────────────────────────────────

    def print_org_chart(self):
        """Print the full agent hierarchy."""
        self._section("LEGACY COMMERCE INC. — AI AGENT HIERARCHY")

        console.print(
            Panel(
                "[bold white]LEGACY COMMERCE INC.[/bold white]\n"
                "[dim]Founded 1975  ·  $15M Revenue  ·  45,000 Customers[/dim]\n"
                "[dim]Shopify + Amazon + eBay + Own Marketplace[/dim]",
                border_style="yellow",
            )
        )

        for tier_name, agents_dict in HIERARCHY.items():
            table = Table(
                title=f"[bold]{tier_name}[/bold]",
                box=box.ROUNDED,
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Agent", style="cyan", width=8)
            table.add_column("Title", style="white", width=35)
            table.add_column("Model", style="green", width=22)
            table.add_column("Reports To", style="yellow", width=12)

            for agent_id, desc in agents_dict.items():
                cfg = AGENT_CONFIGS[agent_id]
                table.add_row(
                    f"{cfg['emoji']} {agent_id}",
                    cfg["title"],
                    cfg["model"],
                    cfg["reports_to"],
                )
            console.print(table)
            console.print()

    # ─────────────────────────────────────────────────────────────────────────
    # MORNING BRIEFING
    # ─────────────────────────────────────────────────────────────────────────

    def morning_briefing(self):
        """ARIA opens the day and each agent gives a status report — using live Shopify data if available."""
        self._section("MORNING BRIEFING — ARIA OPENS THE DAY")

        snap, store_ctx = self._load_store_snapshot()
        today = datetime.now().strftime("%A %B %d, %Y")

        # ARIA's opening statement
        aria_opening_prompt = (
            f"It's {today} at 8:00 AM. Give a powerful 3-sentence opening briefing to your entire "
            "agent team for the week ahead. Reference the 50-year legacy, current revenue goals, "
            "and the priority this week. Motivating but data-grounded."
        )
        if store_ctx:
            aria_opening_prompt = store_ctx + "\n\n" + aria_opening_prompt

        opening = self.aria.think(aria_opening_prompt, max_tokens=250)
        self._print_response(self.aria, opening)

        # Manager-specific data slices
        manager_contexts = {
            "NOVA": store_ctx,
            "LUNA": (
                f"New customers this week: {snap['new_customers_week']:,}\n"
                f"Top products: {', '.join(n for n, _ in snap['top_products'][:3])}\n"
                f"Abandoned carts: {snap['abandoned_count']} worth ${snap['abandoned_value']:,.2f}"
                if snap else ""
            ),
            "ZARA": (
                f"Revenue today: ${snap['revenue_today']:,.2f} ({snap['orders_today']} orders)\n"
                f"Revenue last 7 days: ${snap['revenue_7d']:,.2f} ({snap['orders_7d']} orders)\n"
                f"Avg order value: ${snap['aov']:,.2f}\n"
                f"Top products: {', '.join(n for n, _ in snap['top_products'][:3])}"
                if snap else ""
            ),
            "FELIX": (
                f"Abandoned checkouts: {snap['abandoned_count']} (${snap['abandoned_value']:,.2f} recoverable)\n"
                f"New customers this week: {snap['new_customers_week']:,}\n"
                f"Total customers: {snap['total_customers']:,}"
                if snap else ""
            ),
            "CIPHER": store_ctx,
            "REX": (
                self.shopify.format_inventory_context(snap)
                if snap else ""
            ),
        }

        # Status reports from managers only
        manager_ids = ["NOVA", "LUNA", "ZARA", "FELIX", "CIPHER", "REX"]
        self._section("MANAGER STATUS REPORTS")

        for agent_id in manager_ids:
            agent = self.agents[agent_id]
            console.print(f"\n[bold]{agent.emoji} {agent.name} — {agent.title}[/bold]")
            ctx = manager_contexts.get(agent_id, "")
            if ctx:
                prompt = (
                    f"{ctx}\n\nGive a 4-line status report for today's morning briefing.\n"
                    "Format exactly:\n"
                    "FOCUS: [what you're working on today based on the real data above]\n"
                    "PRIORITY: [top revenue task this week]\n"
                    "RISK: [any concern or blocker]\n"
                    "OPPORTUNITY: [revenue opportunity you're watching]\n\n"
                    "Be specific to the real store data. No fluff."
                )
                report = agent.think(prompt, max_tokens=250)
            else:
                report = agent.status_report()
            console.print(f"[dim]{report}[/dim]")

        # ARIA closes the briefing
        self._section("ARIA'S DIRECTIVES FOR THE WEEK")
        directives_prompt = (
            "Based on the store data and your team's status reports, give 5 specific directives. "
            "Each directive should name the agent responsible and a concrete action with a measurable target. "
            "Format: AGENT → Action. Be specific and revenue-focused."
        )
        if store_ctx:
            directives_prompt = store_ctx + "\n\n" + directives_prompt

        directives = self.aria.think(directives_prompt, max_tokens=400)
        self._print_response(self.aria, directives)

        self.telegram.send(self.telegram.briefing_summary(snap))

    # ─────────────────────────────────────────────────────────────────────────
    # INCOME IDEAS EVALUATION
    # ─────────────────────────────────────────────────────────────────────────

    def evaluate_income_ideas(self, top_n: int = 5):
        """
        ARIA selects the top ideas, then relevant agents evaluate them.
        Returns a prioritized action plan.
        """
        self._section("INCOME STRATEGY EVALUATION — ARIA LEADS THE SESSION")

        # ARIA opens the evaluation
        aria_intro = self.aria.think(
            f"You're leading a strategy session to evaluate our top real-time income generation "
            f"ideas. We have 22 ideas across automation, new channels, retention, and optimization. "
            f"As CRO, what are your 3 evaluation criteria for picking the right ideas to launch? "
            f"And which categories excite you most for immediate impact?",
            max_tokens=300,
        )
        self._print_response(self.aria, aria_intro)

        # Evaluate quick wins (low investment, high convenience)
        self._section(f"TOP {top_n} QUICK WIN IDEAS — AGENT EVALUATIONS")

        ideas_to_evaluate = QUICK_WINS[:top_n]

        scores: list[dict] = []

        for idea in ideas_to_evaluate:
            console.print(
                Panel(
                    f"[bold]#{idea['id']}: {idea['name']}[/bold]\n"
                    f"[dim]{idea['description'][:120]}...[/dim]\n\n"
                    f"💰 Revenue Potential: {idea['revenue_potential']}\n"
                    f"⚡ Convenience Score: {idea['convenience_score']}/10\n"
                    f"⏱  Time to Revenue: {idea['time_to_revenue']}\n"
                    f"💵 Investment: {idea['investment_level']}",
                    border_style="yellow",
                )
            )

            # Primary owner evaluates
            primary_id = idea["primary_owner"]
            if primary_id in self.agents:
                primary_agent = self.agents[primary_id]
                console.print(
                    f"\n[bold cyan]→ {primary_agent.emoji} {primary_agent.name} evaluates:[/bold cyan]"
                )
                evaluation = primary_agent.evaluate_income_idea(idea)
                console.print(f"[white]{evaluation}[/white]\n")

            # One supporting agent adds perspective
            if idea["supporting_agents"]:
                support_id = idea["supporting_agents"][0]
                if support_id in self.agents:
                    support_agent = self.agents[support_id]
                    console.print(
                        f"[bold green]→ {support_agent.emoji} {support_agent.name} adds:[/bold green]"
                    )
                    support_view = support_agent.evaluate_income_idea(idea)
                    console.print(f"[dim]{support_view}[/dim]\n")

            scores.append(
                {
                    "id": idea["id"],
                    "name": idea["name"],
                    "convenience": idea["convenience_score"],
                    "investment": idea["investment_level"],
                    "time": idea["time_to_revenue"],
                    "potential": idea["revenue_potential"],
                }
            )

        # ARIA's final verdict
        self._section("ARIA'S FINAL VERDICT & ACTION ORDER")

        ideas_summary = "\n".join(
            [
                f"#{s['id']}: {s['name']} | Score: {s['convenience']}/10 | "
                f"Investment: {s['investment']} | Time: {s['time']}"
                for s in scores
            ]
        )

        verdict = self.aria.think(
            f"You've just heard your team evaluate the top quick-win income ideas:\n\n"
            f"{ideas_summary}\n\n"
            f"As CRO, give your final prioritized launch order (1-{len(scores)}), "
            f"the agent responsible for each, a 30-day revenue target for each, "
            f"and your single non-negotiable requirement for the #1 priority. "
            f"Be decisive and specific.",
            max_tokens=500,
        )
        self._print_response(self.aria, verdict)

    # ─────────────────────────────────────────────────────────────────────────
    # TASK DELEGATION
    # ─────────────────────────────────────────────────────────────────────────

    def delegate_tasks(self):
        """ARIA delegates key tasks down the hierarchy."""
        self._section("TASK DELEGATION — ARIA ASSIGNS RESPONSIBILITIES")

        tasks = [
            {
                "to": "ZARA",
                "task": "Design and launch our first automated flash sale this week. "
                        "Target: clear 200 units of slow-moving home décor SKUs. "
                        "Coordinate with BLAZE on timing and PRISM on discount depth.",
            },
            {
                "to": "LUNA",
                "task": "Build a 30-day social commerce launch plan for TikTok Shop. "
                        "We need our first 10 shoppable videos live within 2 weeks. "
                        "Leverage the 50-year brand story as our content angle.",
            },
            {
                "to": "HALO",
                "task": "Audit our abandoned cart email sequence. We should be recovering "
                        "at least 18% of abandoned carts. If we're below that, redesign "
                        "the 3-step flow by end of week.",
            },
            {
                "to": "CIPHER",
                "task": "Pull a full attribution report: which channels drove our top 20% "
                        "of revenue last month? Present findings to ARIA by Thursday with "
                        "specific budget reallocation recommendations.",
            },
        ]

        for delegation in tasks:
            agent = self.agents[delegation["to"]]
            console.print(
                f"\n[yellow]👩‍💼 ARIA → {agent.emoji} {agent.name}:[/yellow]"
            )
            console.print(f"[bold white]Task:[/bold white] {delegation['task']}\n")
            response = agent.receive_task("ARIA", delegation["task"])
            console.print(
                Panel(response, title=f"[cyan]{agent.emoji} {agent.name} responds[/cyan]",
                      border_style="cyan", padding=(0, 2))
            )

    # ─────────────────────────────────────────────────────────────────────────
    # TRAINING SESSIONS
    # ─────────────────────────────────────────────────────────────────────────

    def run_training_session(self):
        """Train each agent on a high-stakes scenario from their domain."""
        self._section("AGENT TRAINING SESSION — SCENARIO-BASED DRILLS")

        training_scenarios = {
            "BLAZE": (
                "Our biggest competitor just launched a 48-hour 40%-off sitewide sale "
                "and it's going viral on TikTok. We have inventory and margin to respond. "
                "What do you do in the next 2 hours?"
            ),
            "JADE": (
                "A customer with 8 orders over 3 years just posted a viral complaint on "
                "Twitter saying their last order was damaged and we ghosted them. "
                "The tweet has 1,200 likes. How do you handle this right now?"
            ),
            "CIPHER": (
                "Our conversion rate dropped 22% this week with no apparent changes to "
                "the site. Traffic is up 15%. How do you diagnose this and what's your "
                "first hypothesis?"
            ),
            "VEIL": (
                "We're seeing 40 orders in 3 hours from different new accounts all shipping "
                "to the same ZIP code with different credit cards. Order values are all "
                "$87-$93. What do you do?"
            ),
            "PRISM": (
                "A competitor just matched our price on our top 5 bestsellers within 30 minutes "
                "of us adjusting. We suspect they're scraping us in real-time. "
                "How do you respond strategically?"
            ),
        }

        for agent_id, scenario in training_scenarios.items():
            agent = self.agents[agent_id]
            console.print(
                Panel(
                    f"[bold yellow]SCENARIO:[/bold yellow] {scenario}",
                    title=f"[bold]{agent.emoji} {agent.name} Training Drill[/bold]",
                    border_style="yellow",
                )
            )
            response = agent.train_on_scenario(scenario)
            console.print(
                Panel(
                    response,
                    title=f"[cyan]{agent.emoji} {agent.name}'s Response[/cyan]",
                    border_style="cyan",
                    padding=(1, 2),
                )
            )
            console.print()

        # ARIA grades the training
        self._section("ARIA'S TRAINING FEEDBACK")
        feedback = self.aria.think(
            "You just watched your team handle 5 tough scenarios: a competitor flash sale, "
            "a viral complaint, a conversion drop mystery, a fraud alert, and a price scraping "
            "attack. Give 3 sentences of overall feedback on your team's readiness, and call out "
            "one area where you want sharper execution.",
            max_tokens=200,
        )
        self._print_response(self.aria, feedback)

    # ─────────────────────────────────────────────────────────────────────────
    # AGENT ACTIONS — REAL SHOPIFY OPERATIONS
    # ─────────────────────────────────────────────────────────────────────────

    def blaze_flash_sale(self, instruction: str = None):
        """BLAZE creates a real flash sale discount code on Shopify."""
        self._section("BLAZE — LAUNCHING FLASH SALE")
        blaze = self.agents["BLAZE"]
        tools = TOOLS_BY_AGENT["BLAZE"]

        task = instruction or (
            "Analyze our store situation and create a compelling flash sale right now. "
            "First check what active promotions we already have (don't create duplicates). "
            "Then create a new flash sale discount code — pick a discount percentage (15-25%) "
            "and duration (4-8 hours) that makes sense for an ecommerce flash sale. "
            "Give the code a punchy name. After creating it, summarize what you did and "
            "how to promote it."
        )

        console.print(f"[yellow]Task:[/yellow] {task}\n")
        result = blaze.act(task, tools, self.tool_runner, max_tokens=1200)
        self._print_response(blaze, result)
        self.telegram.send(self.telegram.flash_sale_summary(result))

    def prism_price_audit(self, instruction: str = None):
        """PRISM audits current prices and optionally adjusts them."""
        self._section("PRISM — PRICE INTELLIGENCE AUDIT")
        prism = self.agents["PRISM"]
        tools = TOOLS_BY_AGENT["PRISM"]

        task = instruction or (
            "Pull our full product catalog with current prices. Analyze the pricing strategy: "
            "identify any products that look underpriced vs their category, any that might "
            "benefit from a compare_at_price to show a 'sale' display, and give me your "
            "top 3 pricing recommendations. Don't make any changes unless you're highly "
            "confident — report findings first."
        )

        console.print(f"[yellow]Task:[/yellow] {task}\n")
        result = prism.act(task, tools, self.tool_runner, max_tokens=1200)
        self._print_response(prism, result)
        self.telegram.send(self.telegram.price_audit_summary())

    def halo_cart_recovery(self, instruction: str = None):
        """HALO scans abandoned checkouts and builds a recovery plan with a real discount code."""
        self._section("HALO — ABANDONED CART RECOVERY")
        halo = self.agents["HALO"]
        tools = TOOLS_BY_AGENT["HALO"]

        task = instruction or (
            "Pull all abandoned checkouts from our store right now. "
            "Analyse the data: how many carts, total recoverable value, what products "
            "people are abandoning. Then create a recovery discount code (10% off, "
            "expires in 48 hours, limited to 100 uses) that we can send to these customers. "
            "Finally, write the exact subject line and first paragraph of the recovery email "
            "I should send to the highest-value abandoned cart customer."
        )

        console.print(f"[yellow]Task:[/yellow] {task}\n")
        result = halo.act(task, tools, self.tool_runner, max_tokens=1500)
        self._print_response(halo, result)
        self.telegram.send(self.telegram.cart_recovery_summary(snap if hasattr(self, '_last_snap') else None))

    # ─────────────────────────────────────────────────────────────────────────
    # FULL RUN
    # ─────────────────────────────────────────────────────────────────────────

    def run_full_session(self):
        """Execute the complete manager workflow: org chart → briefing → evaluation → delegation → training."""
        console.print(
            Panel(
                "[bold yellow]LEGACY COMMERCE INC.[/bold yellow]\n"
                "[white]AI Agent Management System[/white]\n"
                "[dim]50 Years of Commerce · Now Running 24/7 with 15 AI Agents[/dim]",
                border_style="yellow",
                padding=(1, 4),
            )
        )
        self.print_org_chart()
        self.morning_briefing()
        self.evaluate_income_ideas(top_n=5)
        self.delegate_tasks()
        self.run_training_session()

        # Final summary from ARIA
        self._section("ARIA'S CLOSING SUMMARY")
        summary = self.aria.think(
            "Summarize today's session in 4 bullet points: "
            "what was accomplished, what's in motion, what you're most excited about, "
            "and your single biggest concern going into next week.",
            max_tokens=250,
        )
        self._print_response(self.aria, summary)
