"""
Agent Factory — All 15 AI Agents for Legacy Commerce Inc.
Each agent wraps the Anthropic SDK with a unique personality and domain expertise.
"""

import anthropic
from config import AGENT_CONFIGS, BUSINESS_CONTEXT


class BaseAgent:
    """
    Foundation class for every Legacy Commerce agent.
    Wraps the Anthropic SDK with personality, memory, and ecommerce context.
    """

    def __init__(self, agent_id: str, client: anthropic.Anthropic):
        cfg = AGENT_CONFIGS[agent_id]
        self.id = agent_id
        self.name = cfg["full_name"]
        self.title = cfg["title"]
        self.level = cfg["level"]
        self.model = cfg["model"]
        self.personality = cfg["personality"]
        self.reports_to = cfg["reports_to"]
        self.manages = cfg["manages"]
        self.emoji = cfg["emoji"]
        self.catchphrase = cfg["catchphrase"]
        self.client = client
        self._conversation: list[dict] = []

    # ── Internals ────────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        manages_str = (
            f"Direct reports: {', '.join(self.manages)}"
            if self.manages
            else "Individual contributor (no direct reports)"
        )
        return f"""{self.personality}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPANY CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{BUSINESS_CONTEXT}

YOUR ORG POSITION:
- Level: {self.level}
- Reports to: {self.reports_to}
- {manages_str}

BEHAVIOR RULES:
- Always stay in character as {self.name}
- Your catchphrase is: "{self.catchphrase}" — use it naturally, not robotically
- Be concise, actionable, and opinionated
- Speak from genuine domain expertise, not generic advice
- When you disagree with something, say so professionally
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    def _call(self, messages: list[dict], max_tokens: int = 800) -> str:
        thinking_config = (
            {"type": "adaptive"} if self.level == "C-Suite" else None
        )
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": self._system_prompt(),
            "messages": messages,
        }
        if thinking_config:
            kwargs["thinking"] = thinking_config

        response = self.client.messages.create(**kwargs)
        # Extract text blocks only (skip thinking blocks)
        return next(
            (b.text for b in response.content if b.type == "text"), ""
        )

    def act(self, task: str, tools: list, tool_runner, max_tokens: int = 1000, max_iters: int = 6) -> str:
        """
        Agentic tool-use loop: agent reasons, calls real Shopify tools,
        gets results back, and continues until done.
        """
        messages = [{"role": "user", "content": task}]

        for _ in range(max_iters):
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "system": self._system_prompt(),
                "tools": tools,
                "messages": messages,
            }
            # Tool use and thinking conflict — skip thinking for action calls
            response = self.client.messages.create(**kwargs)

            # If done, return the final text
            if response.stop_reason == "end_turn":
                return next((b.text for b in response.content if b.type == "text"), "")

            # If tool_use, execute each tool and feed results back
            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = tool_runner.execute(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "user", "content": tool_results})
                continue

            # Any other stop reason — return what we have
            return next((b.text for b in response.content if b.type == "text"), "")

        return "Agent reached max iterations."

    # ── Public API ────────────────────────────────────────────────────────────

    def think(self, prompt: str, max_tokens: int = 800) -> str:
        """Single-turn thought — no conversation memory."""
        return self._call([{"role": "user", "content": prompt}], max_tokens)

    def chat(self, message: str) -> str:
        """Multi-turn chat with persistent conversation memory."""
        self._conversation.append({"role": "user", "content": message})
        response = self._call(self._conversation)
        self._conversation.append({"role": "assistant", "content": response})
        return response

    def reset_conversation(self):
        """Clear conversation history."""
        self._conversation = []

    def status_report(self) -> str:
        """Return a brief status update formatted for the morning briefing."""
        prompt = f"""Give a 4-line status report for today's morning briefing.
Format exactly:
FOCUS: [what you're working on today]
PRIORITY: [top revenue task this week]
RISK: [any concern or blocker]
OPPORTUNITY: [revenue opportunity you're watching]

Be specific to your role. No fluff."""
        return self.think(prompt, max_tokens=250)

    def evaluate_income_idea(self, idea: dict) -> str:
        """Evaluate an income idea from this agent's professional perspective."""
        prompt = f"""Evaluate this real-time income idea for Legacy Commerce Inc. from your perspective as {self.title}:

IDEA #{idea['id']}: {idea['name']}
━━━━━━━━━━━━━━━━━━━━
{idea['description']}

Investment Level: {idea['investment_level']}
Time to Revenue: {idea['time_to_revenue']}
Revenue Potential: {idea['revenue_potential']}
Convenience Score: {idea['convenience_score']}/10

Provide:
1. YOUR VERDICT: LAUNCH NOW / LAUNCH NEXT QUARTER / SKIP (pick one, be decisive)
2. TOP BENEFIT: What's the single biggest upside from your domain expertise
3. TOP RISK: The #1 thing that could go wrong
4. YOUR ROLE: What you personally need to do to make this work (2 sentences max)

Stay in character. Be direct."""

        return self.think(prompt, max_tokens=350)

    def receive_task(self, from_agent: str, task: str) -> str:
        """Acknowledge a delegated task and outline your action plan."""
        prompt = f"""{from_agent} has delegated this task to you:

"{task}"

Respond professionally:
1. Acknowledge with your honest reaction (enthusiastic? cautious? concerned?)
2. Your 3-step action plan to execute this
3. What you need from {from_agent} or other agents to succeed
4. Estimated timeline

Keep it under 200 words."""
        return self.think(prompt, max_tokens=300)

    def train_on_scenario(self, scenario: str) -> str:
        """Walk through a training scenario relevant to this agent's role."""
        prompt = f"""TRAINING SCENARIO for {self.title}:

{scenario}

Walk through exactly how you would handle this situation. Be specific about:
- Your immediate first action
- Who you'd contact and why
- What metrics you'd track
- How you'd know you succeeded

This is your training session — show your expertise."""
        return self.think(prompt, max_tokens=500)

    def __str__(self) -> str:
        return f"{self.emoji} {self.name} | {self.title} | {self.level}"

    def __repr__(self) -> str:
        return f"Agent(id={self.id!r}, model={self.model!r})"


# ── Agent Factory ─────────────────────────────────────────────────────────────

class AgentFactory:
    """Creates and manages the full fleet of Legacy Commerce agents."""

    @staticmethod
    def create_all(client: anthropic.Anthropic) -> dict[str, BaseAgent]:
        """Instantiate every agent defined in config."""
        return {
            agent_id: BaseAgent(agent_id, client)
            for agent_id in AGENT_CONFIGS
        }

    @staticmethod
    def create_agent(agent_id: str, client: anthropic.Anthropic) -> BaseAgent:
        """Create a single named agent."""
        if agent_id not in AGENT_CONFIGS:
            raise ValueError(
                f"Unknown agent '{agent_id}'. "
                f"Available: {list(AGENT_CONFIGS.keys())}"
            )
        return BaseAgent(agent_id, client)

    @staticmethod
    def create_tier(tier: str, client: anthropic.Anthropic) -> dict[str, BaseAgent]:
        """Create only agents from a specific tier (C-Suite / Manager / Specialist)."""
        return {
            agent_id: BaseAgent(agent_id, client)
            for agent_id, cfg in AGENT_CONFIGS.items()
            if cfg["level"] == tier
        }
