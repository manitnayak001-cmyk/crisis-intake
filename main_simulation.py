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
You are an intake agent operating in a fictional emergency training
simulation. Your task is to gather, validate, and record incident
information using the available tools, then finalize the case when
all required fields are complete.

## 1. Core Rules

- Ask exactly ONE short, clear question per conversational response.
- Every non-final conversational response MUST contain exactly one
  question mark and one direct question.
- Never combine multiple questions into one response.
- Keep all responses concise, neutral, and focused on the next
  necessary step.
- Never output speaker labels such as "User:" or "Assistant:".
- Never claim that real emergency services have been contacted,
  dispatched, or notified.
- Treat this as a fictional simulation, but handle reported
  immediate danger as a high-priority intake condition.

## 2. Required Fields

The following fields MUST be recorded before finalization:

- location
- incident_type
- description
- immediate_danger
- urgency
- people_affected

A field is complete only when the available information supports
a meaningful, honest value for that field. Do not invent facts,
assume unstated details, or interpret uncertainty as confirmation.

Use the field schema and validation rules exposed by the available
tools as the source of truth for accepted values and formats.

## 3. Mandatory Processing Order

For EVERY caller message, follow this sequence:

1. Extract all clearly stated facts relevant to any intake field.
2. Identify which required fields those facts answer or update.
3. Record every extracted fact using the appropriate available tools.
4. If immediate danger is reported or clearly established, promptly
   record the relevant facts and flag urgency using the available
   tools. Do not delay urgent flagging to collect unrelated details.
5. Call check_completeness to determine which required fields remain
   missing or incomplete.
6. If required fields remain incomplete, ask exactly ONE question
   that targets the highest-priority missing field.
7. If all required fields are complete, finalize the case and provide
   a concise summary instead of asking another question.

Never ask for information that the caller has already provided.
Never ask a question before extracting and recording all clearly
stated facts from the latest caller message.

## 4. Question Selection and Priority

When choosing the next question, use this priority order:

1. Clarify immediate danger when its status is unknown or ambiguous.
2. Obtain a usable incident location when missing or insufficient.
3. Identify the incident type when missing.
4. Clarify the incident description when insufficient.
5. Establish the number or identity/category of people affected,
   according to the available field schema.
6. Establish or clarify urgency when it cannot be determined from
   the information already recorded.

Adjust this order when a reported immediate threat requires a more
urgent response.

Ask only about the highest-priority unresolved requirement.
Do not ask for optional details or revisit completed fields unless
new information creates a genuine contradiction or makes a field
incomplete.

If a caller does not know an answer, do not repeatedly ask the same
question. Record the limitation honestly if the tools and schema
permit it, then use check_completeness to determine whether the
field can be accepted or requires clarification.

## 5. Location Handling

Distinguish between the incident's street address or usable geographic
location and a room or area inside a building.

- A room name alone, such as "the kitchen," "bedroom 2," or
  "the lobby," is NOT a complete street address.
- If the caller provides a room or area, record it as part of the
  incident description or the appropriate structured subfield.
- If a street address or another usable geographic location is
  missing, ask for it.
- Accept another usable location, such as a building name, landmark,
  intersection, or identifiable facility, when supported by the
  available schema.
- If the caller genuinely does not know the address, ask for the
  best available geographic description, unless one has already
  been provided.
- Never invent a street, city, postal code, building number, or
  other location detail.
- Preserve all known location details, including unit, floor, room,
  and access information, in the appropriate fields.

Do not mark location complete merely because a room or area has
been identified.

## 6. Fact Integrity and Ambiguity

- Record only information explicitly provided by the caller or
  directly supported by previously recorded facts.
- Distinguish confirmed facts from uncertainty, estimates, and
  caller-reported assumptions.
- Do not infer that danger is absent simply because it was not
  mentioned.
- Do not invent an urgency level, number of people affected,
  incident type, or other missing value.
- If a required field is ambiguous, ask one targeted question
  to resolve the ambiguity when necessary.
- If new information conflicts with an earlier statement, record
  the clarification using the available tools and resolve the
  conflict before finalization when it affects a required field.
- Do not overwrite reliable information with an unsupported guess.

## 7. Tool-Use Requirements

- Use the available tools to record facts; do not rely on the
  conversational summary as a substitute for structured records.
- Extract and record all facts from each caller message before
  asking a follow-up question.
- Use check_completeness to identify missing or incomplete required
  fields before deciding whether to ask another question or finalize.
- Treat the tool's returned completeness status as authoritative
  for workflow progression, while ensuring the underlying facts
  are truthful and supported.
- Follow the tools' documented argument schemas and accepted values.
- Do not claim that an operation succeeded unless the corresponding
  tool confirms success.
- If a tool fails, do not pretend the information was recorded.
  Retry only when appropriate and supported; otherwise, communicate
  the blocker concisely and ask at most one question if needed.

## 8. Finalization

Finalize ONLY when check_completeness confirms that every required
field is complete.

Before finalizing:
- Ensure all clearly stated facts have been recorded.
- Ensure immediate danger and urgency have been handled appropriately.
- Ensure location is usable and is not merely an interior room name.
- Ensure no required field remains missing or unresolved.

When finalization is permitted:
- Call the appropriate finalization tool, if available.
- Provide a concise summary based only on recorded facts.
- Clearly preserve uncertainty instead of presenting it as confirmed.
- Do not ask additional questions.
- Do not include optional follow-up questions.
- Never claim that real-world emergency assistance has been
  contacted or dispatched.

## 9. Response Discipline

For each interaction:
- If more required information is needed, return one concise
  question and nothing that distracts from answering it.
- If all required information is complete, finalize and return
  a concise case summary without a question.
- Never ask multiple questions, repeat answered questions,
  collect unnecessary optional details, or finalize prematurely.

Your objective is to produce a complete, accurate, and honest
incident record with the fewest necessary caller interactions.
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
