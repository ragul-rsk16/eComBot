import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

for path in (str(PROJECT_ROOT), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from src.tools.order_tools import get_order_status
from src.utils.prompt_loader import load_prompt
from src.tools.user_tools import build_greeting,save_user_name

_MODEL = "openrouter/openai/gpt-4o-mini"

PROMPTS_DIR = SRC_DIR / "prompts"
COMMON_PROMPT = load_prompt(str(PROMPTS_DIR / "common.md"))
CREATIVE_PROMPT = load_prompt(str(PROMPTS_DIR / "polite_creative.md"))

root_agent = LlmAgent(
    model=LiteLlm(model=_MODEL),
    name='root_agent',
    description='A helpful e-commerce assistant for customers of RSK Enterprises.',
    instruction=f"""{COMMON_PROMPT}""".strip(),
    tools=[get_order_status,save_user_name,build_greeting],
    #instruction=f"""{CREATIVE_PROMPT}""".strip(),
)