import os
import json
from openai import AsyncOpenAI
from tools import TOOLS, call_tool

MODEL = "llama-3.3-70b-versatile"

_client = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY"),
        )
    return _client


SYSTEM_PROMPT = "Ти асистент інтернет-магазину Apple-техніки. Відповідай коротко і по справі."


async def process_message(messages: list, user_text: str, user_id: int) -> str:
    """
    Append user_text to messages, run the agentic loop, return assistant reply.
    messages list is mutated in place so the caller can maintain history.
    """
    client = get_client()
    messages.append({"role": "user", "content": user_text})

    while True:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            reply = msg.content or ""
            messages.append({"role": "assistant", "content": reply})
            return reply

        # Handle tool calls
        messages.append(msg)
        for call in msg.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments)
            result = call_tool(name, args, user_id)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )


def new_session() -> list:
    return [{"role": "system", "content": SYSTEM_PROMPT}]
