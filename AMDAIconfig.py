Time to start your vLLM server and creating an end-point for your LLM. Let's open a terminal using your Jupyter server. Then run the following command in this terminal to start the vLLM server:

VLLM_USE_TRITON_FLASH_ATTN=0 \
vllm serve Qwen/Qwen3-30B-A3B \
    --served-model-name Qwen3-30B-A3B \
    --api-key abc-123 \
    --port 8000 \
    --enable-auto-tool-choice \
    --tool-call-parser hermes \
    --trust-remote-code
Open another terminal and monitor the GPU utilization by running this command:

watch rocm-smi

#below is setup
import os

BASE_URL = f"http://localhost:8000/v1"

os.environ["BASE_URL"]    = BASE_URL
os.environ["OPENAI_API_KEY"] = "abc-123"   

print("Config set:", BASE_URL)

!pip install -q pydantic-ai-slim openai

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

provider = OpenAIProvider(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)

agent_model = OpenAIChatModel("Qwen3-30B-A3B", provider=provider)

from pydantic_ai import Agent

agent = Agent(
    model=agent_model
)

import asyncio
from pydantic_ai.mcp import MCPServerStdio
async def run_async(prompt: str) -> str:
    async with agent.run_mcp_servers():
        result = await agent.run(prompt)
        return result.output

await run_async("What is the capital of France?")

await run_async("What’s the date today?")

from datetime import datetime
from pydantic_ai import Tool          
@Tool
def get_current_date() -> str:
    """Return the current date/time as an ISO-formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = Agent(
    model=agent_model,
    tools=[get_current_date],
    system_prompt = (
        "You have access to:\n"
        "   1. get_current_time(params: dict)\n"
        "Use this tool for date/time questions."
    )
)

await run_async("What’s the date today?")
