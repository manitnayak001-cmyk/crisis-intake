from llm import chat
# from models import CaseFile
from agents.tools import update_case_field, TOOLS

messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful assistant that records information from a caller "
            "into a case file. You will be provided with a list of tools you can use "
            "to update the case file. Only use the tools provided, and only record "
            "information that the caller actually provides."
        ),
    },
    {
        "role": "user",
        "content": "hi, my name is manit and i am caling to report a fire in my house. please send help.",
    }
]

response = chat(messages, tools=TOOLS)

message = response.choices[0].message

print("AI Response:", message.content)
print("tool calls:", message.tool_calls)

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