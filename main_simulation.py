import json
from pathlib import Path

from llm import chat
from models import CaseFile
from agents.tools import TOOLS, execute_tool, check_completeness, is_case_complete
from agents.caller_agent import load_scenario, generate_caller_response
from database import init_db, save_case




MAX_TURNS = 12


def build_intake_prompt() -> str:
    return """
You are an intake agent in a fictional emergency training simulation.

Your responsibilities:
- Collect incident information from the caller.
- Record facts using the available tools.
- Ask exactly one short question at a time.
- Record only facts the caller has provided.
- If immediate danger is reported, flag urgency promptly.
- Use check_completeness tool to identify missing required information.
- Extract every clearly stated fact before asking another question.
- Never finalize while a required field is missing.
- When all required fields are collected, finalize the case with a
  concise summary.
- Distinguish the incident's street address from a room or area inside a building.
- If the caller provides only a room or area, such as "the kitchen",
  record it as part of the incident description.
- Do not treat a room name as a complete street address.
- Ask for the street address or another usable location if it is missing.
- If the caller genuinely does not know the address, record the best
  available location honestly without inventing details.
- Each conversational response must contain exactly one question.
- Never combine multiple questions into one response.
- Do not repeat questions already answered by the caller.
- If several facts are available in the caller's response, extract them
  using tools before asking for any additional information.
- Do not ask for optional information once all required fields are complete.
- Never claim that real emergency services have been contacted or dispatched.
- Never output speaker labels such as "User:" or "Assistant:".

Required fields:
- location
- incident_type
- description
- immediate_danger
- urgency
- people_affected

Keep responses concise and focused on the next important step.
"""


def build_summary(case: CaseFile) -> str:
    return (
        f"Incident: {case.incident_type}. "
        f"Location: {case.location}. "
        f"Description: {case.description}. "
        f"Immediate danger: "
        f"{'Yes' if case.immediate_danger else 'No'}. "
        f"Urgency: {case.urgency}."
    )



def finalize_if_complete(case: CaseFile) -> bool:
    """Finalize and persist a complete case."""

    if not is_case_complete(case):
        return False

    if case.status != "finalized":
        result = execute_tool(
            case=case,
            tool_name="finalize_case",
            arguments=json.dumps({"summary": build_summary(case)}),
        )

        print("\nFinalization result:", result)

        if not result.get("success"):
            return False

    case_id = save_case(case)
    print(f"Case saved to SQLite with ID: {case_id}")

    return True



def run_simulation():
    init_db()
    scenario_path = (
        Path(__file__).parent / "scenarios" / "road_accident.json"
    )
    scenario = load_scenario(str(scenario_path))

    case = CaseFile()

    initial_message = scenario["initial_message"]

    # Conversation history used by the intake agent.
    intake_messages = [
        {
            "role": "system",
            "content": build_intake_prompt(),
        },
        {
            "role": "user",
            "content": initial_message,
        },
    ]

    # Conversation history used by the caller simulator.
    # For this model, assistant represents the fictional caller,
    # while user represents the intake agent asking questions.
    caller_history = [
        {
            "role": "assistant",
            "content": initial_message,
        }
    ]

    print("\n=== CRISIS INTAKE TRAINING SIMULATOR ===")
    print(f"\nCaller: {initial_message}")

    for turn in range(MAX_TURNS):
        print(f"\n--- Turn {turn + 1} ---")

        response = chat(intake_messages, tools=TOOLS)
        message = response.choices[0].message

        # The intake agent wants to execute one or more tools.
        if message.tool_calls:
            intake_messages.append(message)

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"\nTool: {tool_name}")
                print(f"Arguments: {arguments}")

                result = execute_tool(
                    case=case,
                    tool_name=tool_name,
                    arguments=arguments,
                )

                print(f"Result: {result}")

                intake_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )

            # Stop if the LLM has already finalized the case.
            if case.status == "finalized":
                case_id = save_case(case)
                print(f"Case saved to SQLite with ID: {case_id}")
                print("\nCase successfully finalized.")
                break

            # Python enforces the completion condition independently.
            if finalize_if_complete(case):
                print("\nCase successfully finalized.")
                break

            # Let the intake agent process tool results before
            # asking the caller another question.
            continue

        # The intake agent has produced a conversational response.
        intake_reply = message.content or ""
        print(f"\nIntake Agent: {intake_reply}")

        intake_messages.append(message)

        if finalize_if_complete(case):
            print("\nCase successfully finalized.")
            break

        # The caller simulator answers the intake agent's question.
        caller_history.append(
            {
                "role": "user",
                "content": intake_reply,
            }
        )

        caller_reply = generate_caller_response(
            scenario=scenario,
            conversation_history=caller_history,
        )

        print(f"\nCaller: {caller_reply}")

        caller_history.append(
            {
                "role": "assistant",
                "content": caller_reply,
            }
        )

        intake_messages.append(
            {
                "role": "user",
                "content": caller_reply,
            }
        )

    print("\n=== FINAL CASEFILE ===")
    print(case.model_dump_json(indent=2))

    print("\n=== COMPLETENESS ===")
    print(json.dumps(check_completeness(case), indent=2))


if __name__ == "__main__":
    run_simulation()
