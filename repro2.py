from llama_stack_client import LlamaStackClient
import os

MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
messages = [{
    "role": "user",
    "content": "What is the weather in San Francisco?" * 6000,
}]

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

response = client.inference.chat_completion(
    model_id=MODEL_ID,
    messages=messages,
)

print(response.completion_message.content)