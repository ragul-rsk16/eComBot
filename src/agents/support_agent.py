import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

for path in (str(PROJECT_ROOT), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.readonly_context import ReadonlyContext
#from src.tools.order_tools import get_order_status
from src.utils.prompt_loader import load_prompt
from src.rag.embed_catalog import semantic_search
#from src.tools.user_tools import build_greeting,save_user_name
from google.adk.agents import BaseAgent

# ── Model identifiers (single source of truth) ─────────────────────────────
FAST_MODEL   = "openrouter/google/gemini-2.5-flash"  # fast, cost-effective
DEEP_MODEL   = "openrouter/google/gemini-2.5-pro"    # stronger reasoning, higher cost
BACKUP_MODEL = "openrouter/openai/gpt-4o-mini"       # cross-provider fallback
#_MODEL = "openrouter/openai/gpt-4o-mini"
_MODEL = "openrouter/google/gemini-2.5-flash"

_TOP_K = 3

_PERSONA = """
You are Tony Stark, a concise and friendly travel assistant.
Keep answers short, warm, and to the point.
""".strip()

# ── RAG-grounded agent ───────────────────────────────────────────────────────
_GROUNDING_RULES = """
Grounding rules:
- Answer ONLY using the "Retrieved context" section below — never fall back
  on general or remembered knowledge for it, even if you believe you know
  the answer. Treat the retrieved text as the single source of truth.
- If that section says nothing relevant was found, say so plainly — for
  example "I don't have grounded information on that" — instead of
  guessing or inventing an answer.
""".strip()

PROMPTS_DIR = SRC_DIR / "prompts"
COMMON_PROMPT = load_prompt(str(PROMPTS_DIR / "common.md"))
CREATIVE_PROMPT = load_prompt(str(PROMPTS_DIR / "polite_creative.md"))

# ── Routing helpers (moved to src/rag/routing.py) ─────────────────────────
from src.rag.routing import classify_query

def _format_context(results: list[dict]) -> str:
    """Render retrieved chunks (or their absence) as an instruction section."""
    if not results:
        return (
            "Retrieved context: NOTHING RELEVANT FOUND.\n"
            "Follow the fallback rule above — say plainly that you don't have "
            "grounded information on this topic."
        )
    lines = ["Retrieved context (ground your answer in this only):"]
    for r in results:
        lines.append(f"- (similarity={r['score']:.2f}) {r['text']}")
    return "\n".join(lines)


def _build_instruction(ctx: ReadonlyContext) -> str:
    """
    InstructionProvider: runs once per turn, before the model is called.

    Pulls the latest user message out of the invocation context, retrieves
    the closest knowledge-base chunks for it, and appends them — plus the
    grounding rules — to the persona, so the model answers from real
    retrieved text rather than its own memory.
    """
    query = ""
    if ctx.user_content and ctx.user_content.parts:
        query = "".join(part.text or "" for part in ctx.user_content.parts if part.text)

    print(f"query : {query}")
    results = semantic_search(query, top_k=_TOP_K) if query.strip() else []
    print(f"results : {results}")
    print(f"final : {_PERSONA}\n\n{_GROUNDING_RULES}\n\n{_format_context(results)}")
    return f"{_PERSONA}\n\n{_GROUNDING_RULES}\n\n{_format_context(results)}"


# fast-faq route — cheaper, lower-latency model for FAQ queries
product_agent = LlmAgent(
    name="tony_product",
    model=LiteLlm(model=FAST_MODEL),
    instruction=_build_instruction,
    description="Tony stark on the product route.",
)

# deep-planning route — stronger model for complex itinerary planning
faq_agent = LlmAgent(
    name="tony_faq",
    model=LiteLlm(model=DEEP_MODEL),
    instruction=_build_instruction,
    description="Tony stark on faq route.",
)

general_agent = LlmAgent(
    model=LiteLlm(model=BACKUP_MODEL),
    name='root_agent',
    #description='A helpful e-commerce assistant for customers of RSK Enterprises.',
    description=(
        "Tony Stark with RAG — retrieves the top-k matching knowledge-base chunks "
        "for every message and grounds answer in them."
    ),
    #instruction=f"""{COMMON_PROMPT}""".strip(),
    instruction=_build_instruction,
    #tools=[get_order_status,save_user_name,build_greeting],
    #instruction=f"""{CREATIVE_PROMPT}""".strip(),
)

class RouterAgent(BaseAgent):

    async def _run_async_impl(self, ctx):

        try:
            if ctx.user_content and ctx.user_content.parts:
                query = "".join(part.text or "" for part in ctx.user_content.parts if part.text)
        except Exception:
            # defensive: fall back to an empty string which routes to root_agent
            query = ""

        route = classify_query(query)
        print(f"query for classification : {query}")
        print(f"route : {route}")

        if route == "products":
            async for event in product_agent.run_async(ctx):
                yield event

        elif route == "faq":
            async for event in faq_agent.run_async(ctx):
                yield event

        else:
            async for event in general_agent.run_async(ctx):
                yield event


root_agent = RouterAgent(
    name="router"
)