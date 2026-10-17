import json
from pathlib import Path

from llm import chat


def load_scenario(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_caller_response(
    scenario: dict,
    conversation_history: list[dict],
) -> str:
    system_prompt = f"""
You are playing a fictional caller in a training simulation.

Scenario facts:
{json.dumps(scenario, indent=2)}

Your personality:
{scenario["personality"]}

Rules:
- Respond as the caller, in first person.
- Reveal information naturally when asked.
- Do not volunteer every scenario fact immediately.
- Do not invent facts that contradict the scenario.
- If you don't know a requested detail, say you don't know.
- Keep responses short and realistic.
- Never claim that real emergency services have been contacted.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_history,
    ]

    response = chat(messages, temperature=0.7)

    return response.choices[0].message.content or ""