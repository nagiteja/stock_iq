import asyncio

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
from google.genai import types

from setup_api_key import load_gemini_api_key

def build_agent() -> Agent:
    retry_config = types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,  # Initial delay before first retry (in seconds)
        http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
    )

    agent = Agent(
        name="helpful_assistant",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config,
        ),
        description="A simple agent that can answer general questions.",
        instruction="You are a helpful assistant. Use Google Search for current info or if unsure.",
        tools=[google_search],
    )
    return agent


async def main() -> None:
    load_gemini_api_key()
    root_agent = build_agent()
    runner = InMemoryRunner(agent=root_agent)
    response = await runner.run_debug(
        "When is Singapore's independence day?"
    )
    print("Done")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
