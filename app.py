from litellm import completion

model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"
# model = "gpt-4o"

response = completion(
    model=model,
    messages=[{"role": "user", "content": "Hello, how are you?"}],
)

print(response)