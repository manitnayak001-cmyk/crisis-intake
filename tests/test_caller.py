from agents.caller_agent import (
    load_scenario,
    generate_caller_response,
)


scenario = load_scenario("scenarios/fire_at_home.json")

conversation_history = [
    {
        "role": "assistant",
        "content": "where are you calling from?",
    }
]

reply = generate_caller_response(
    scenario,
    conversation_history,
)

print("Caller:", reply)