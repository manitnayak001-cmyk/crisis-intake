import os

from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq


load_dotenv()

# client = OpenAI(
#     base_url=os.environ["LLM_BASE_URL"],
#     api_key=os.environ["LLM_API_KEY"],
# )

client = Groq(
    api_key=os.environ["LLM_API_KEY"],
)
MODEL = os.environ["LLM_MODEL"]


def chat(messages, tools=None, temperature=0.3):
    return client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        temperature=temperature,
    )