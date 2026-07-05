import sys
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from utils.prompt_loader import load_prompt

_MODEL = "openrouter/openai/gpt-4o-mini"

SRC_DIR = Path(__file__).parent.parent
PROMPTS_DIR = SRC_DIR / "prompts"
COMMON_PROMPT = load_prompt(str(PROMPTS_DIR / "common.md"))
CREATIVE_PROMPT = load_prompt(str(PROMPTS_DIR / "polite_creative.md"))

root_agent = LlmAgent(
    model=LiteLlm(model=_MODEL),
    name='root_agent',
    description='A helpful e-commerce assistant for customers of RSK Enterprises.',
    instruction=f"""{COMMON_PROMPT}""".strip(),
    #instruction=f"""{CREATIVE_PROMPT}""".strip(),
)