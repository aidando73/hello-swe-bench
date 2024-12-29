from litellm import completion

completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello, how are you?"}],
)
