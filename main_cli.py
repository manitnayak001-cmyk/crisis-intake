from llm import chat
from models import CaseFile
from agents.tools import TOOLS, execute_tool, check_completeness


case = CaseFile()
messages = [
    {
        "role": "system",
        "content": (
            " You are an intake assistant in a training simulation. "
            " Record only facts the caller actually provides. "
            " Use the available tools to update the case file. "
            " Ask exactly ONE question at a time. "
            " Never combine multiple questions in one response. "
            " Keep your response to at most two short sentences. "
            " After processing tool results, ask for the next important "
            " missing piece of information. "
            " If the caller describes immediate danger to life or safety, "
            " use flag_urgency immediately before asking additional questions. "
            " Do not claim that emergency services have been contacted "
            " or that help has been dispatched. "
            "After each piece of information is recorded, determine whether the "
            "required fields are complete. "
            "When you believe all required fields have been collected: "
            "1. Call check_completeness. "
            "2. If fields are missing, ask for the most important missing field. "
            "3. If no fields are missing, call finalize_case with a concise summary. "
            "4. Do not ask for optional information once the case is complete."
        ),
    },
    {
        "role": "user",
        "content": "Hi, my name is Manit. There's a fire at 123 Main Street. The kitchen is on fire and two people are inside. Yes, there is immediate danger.",
    }
]

MAX_STEPS = 12


for step in range(MAX_STEPS):
    print(f"\n--- Agent step{step+1} ---")
    response = chat(messages, tools=TOOLS)

    message = response.choices[0].message

    print("AI Response:", message.content)
    print("tool calls:", message.tool_calls)


    # ------------------------------------------------
    # CASE 1: LLM wants to use tools
    # ------------------------------------------------

    if message.tool_calls:
        #add the assistant's tool-call message to the conversation
        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments
            print(f"Executing tool: {tool_name} with arguments: {arguments}")
            result =execute_tool(case=case, tool_name=tool_name, arguments=arguments)
            print(f"Tool result: {result}")

            messages.append(
                {
                    "role":"tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )

        continue

    # ------------------------------------------------
    # CASE 2: LLM produced normal text
    # ------------------------------------------------

    messages.append(message)

    break

message = response.choices[0].message


print("Final case:", case)
print("Case completeness:", check_completeness(case))

# case = CaseFile()
# print("Initial case:", case)

# result = update_case_field(
#     case=case,
#     field="caller_name",
#     value="John Doe",
# )

# print("Updated case:", case)
# print("Result:", result)
# messages = [
#     {
#         "role": "system",
#         "content": "You are a helpful AI engineering tutor.",
#     },
#     {
#         "role": "user",
#         "content": "explain what is an ai agent in 1 line.",
#     }
# ]

# response = chat(messages)
# print(response.choices[0].message.content)