#!/usr/bin/env python3
"""
Legacy Commerce Inc. — AI Agent Management System
Manager Entry Point

Run modes:
  python main.py                   → Full session (all modules)
  python main.py --chart           → Org chart only
  python main.py --briefing        → Morning briefing only
  python main.py --ideas           → Income ideas evaluation only
  python main.py --delegate        → Task delegation only
  python main.py --train           → Training scenarios only
  python main.py --chat AGENT_ID   → Interactive chat with a specific agent
  python main.py --idea-list       → Print all 22 income ideas (no API call)

Agent Actions (require Shopify write scopes):
  python main.py --flash-sale      → BLAZE creates a real flash sale discount code
  python main.py --price-audit     → PRISM audits and reports on product pricing
  python main.py --cart-recovery   → HALO scans abandoned carts + creates recovery code
"""

import sys
import os

# Force UTF-8 on Windows to support emoji and Unicode box characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

load_dotenv()

console = Console()

# ─── Pre-flight check ────────────────────────────────────────────────────────

def check_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key or key == "your_api_key_here":
        console.print(
            Panel(
                "[bold red]ANTHROPIC_API_KEY not set.[/bold red]\n\n"
                "1. Copy [cyan].env.example[/cyan] to [cyan].env[/cyan]\n"
                "2. Add your API key from [link=https://console.anthropic.com]console.anthropic.com[/link]\n"
                "3. Run again",
                title="[red]Setup Required[/red]",
                border_style="red",
            )
        )
        sys.exit(1)

# ─── Idea List (no API needed) ───────────────────────────────────────────────

def print_idea_list():
    from income_ideas import INCOME_IDEAS

    console.print(
        Panel(
            "[bold yellow]22 Real-Time Income Generation Ideas[/bold yellow]\n"
            "[dim]Legacy Commerce Inc. — Full Opportunity Catalog[/dim]",
            border_style="yellow",
        )
    )

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Idea", style="cyan", width=32)
    table.add_column("Category", style="white", width=22)
    table.add_column("Investment", style="green", width=10)
    table.add_column("Time to $", style="yellow", width=14)
    table.add_column("Revenue", style="bold white", width=16)
    table.add_column("Score", style="bold cyan", width=6)
    table.add_column("Owner", style="magenta", width=8)

    for idea in INCOME_IDEAS:
        score_str = f"[bold green]{idea['convenience_score']}/10[/bold green]"
        table.add_row(
            idea["id"],
            idea["name"],
            idea["category"],
            idea["investment_level"],
            idea["time_to_revenue"],
            idea["revenue_potential"],
            score_str,
            idea["primary_owner"],
        )

    console.print(table)

    console.print("\n[bold yellow]📊 Summary:[/bold yellow]")
    from income_ideas import IDEAS_BY_CATEGORY
    for cat, ideas in sorted(IDEAS_BY_CATEGORY.items()):
        console.print(f"  [cyan]{cat}[/cyan]: {len(ideas)} idea(s)")

    console.print(
        "\n[dim]Run [bold]python main.py --ideas[/bold] for full AI evaluation with agent input[/dim]"
    )

# ─── Interactive Chat ─────────────────────────────────────────────────────────

def chat_with_agent(agent_id: str):
    check_api_key()
    from agents import AgentFactory
    import anthropic

    client = anthropic.Anthropic()
    try:
        agent = AgentFactory.create_agent(agent_id.upper(), client)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[bold]{agent.emoji} {agent.name}[/bold]  ·  {agent.title}\n"
            f"[dim]{agent.level}  ·  Reports to: {agent.reports_to}[/dim]\n\n"
            f"[italic]\"{agent.catchphrase}\"[/italic]\n\n"
            f"[dim]Type [bold]quit[/bold] or [bold]exit[/bold] to end session.[/dim]",
            border_style="cyan",
        )
    )

    while True:
        try:
            user_input = console.input("[bold yellow]You:[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.lower() in {"quit", "exit", "q", "bye"}:
            console.print(f"\n[dim]{agent.emoji} {agent.name} signing off.[/dim]\n")
            break

        if not user_input:
            continue

        response = agent.chat(user_input)
        console.print(
            f"\n[bold cyan]{agent.emoji} {agent.name}:[/bold cyan] {response}\n"
        )

# ─── Main Dispatch ────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    # No-API commands
    if "--idea-list" in args or "-l" in args:
        print_idea_list()
        return

    if "--help" in args or "-h" in args:
        console.print(__doc__)
        return

    # Interactive chat
    if "--chat" in args:
        idx = args.index("--chat")
        if idx + 1 < len(args):
            agent_id = args[idx + 1]
            chat_with_agent(agent_id)
        else:
            console.print(
                "[red]Usage: python main.py --chat AGENT_ID\n"
                "Example: python main.py --chat ARIA[/red]"
            )
            console.print(
                f"[dim]Available agents: {', '.join(['ARIA','NOVA','LUNA','ZARA','FELIX','CIPHER','REX','SPARK','ECHO','PRISM','JADE','BLAZE','TEMPO','HALO','VEIL'])}[/dim]"
            )
        return

    # API-based commands — check key first
    check_api_key()

    from orchestrator import ARIAOrchestrator
    manager = ARIAOrchestrator()

    if "--chart" in args:
        manager.print_org_chart()
    elif "--briefing" in args:
        manager.morning_briefing()
    elif "--ideas" in args:
        manager.evaluate_income_ideas(top_n=5)
    elif "--delegate" in args:
        manager.delegate_tasks()
    elif "--train" in args:
        manager.run_training_session()
    elif "--flash-sale" in args:
        manager.blaze_flash_sale()
    elif "--price-audit" in args:
        manager.prism_price_audit()
    elif "--cart-recovery" in args:
        manager.halo_cart_recovery()
    else:
        # Full session — the complete workflow
        manager.run_full_session()


if __name__ == "__main__":
    main()
