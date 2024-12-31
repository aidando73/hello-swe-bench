from llama_stack_client import LlamaStackClient
import os

MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

# messages = [{
#     "role": "user",
#     "content": "What is the weather in San Francisco?" * 6000,
# }]

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

message = """"
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

What is the weather in San Francisco?<|eot_id|><|start_header_id|>assistant<|end_header_id|>


"""

response = client.inference.completion(
    model_id=MODEL_ID,
    content=message,
)

print(response.content)