from litellm import completion

model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"
# model = "gpt-4o"

import subprocess

# Run tree command on django directory
try:
    result = subprocess.run(['tree', 'django', '-L', '4'], capture_output=True, text=True)
    tree_output = result.stdout
except FileNotFoundError:
    tree_output = "Error: 'tree' command not found or django directory does not exist"

# Set the tree output as the prompt
prompt = tree_output
# print(prompt)

response = completion(
    model=model,
    messages=[{"role": "user", "content": (
        "<file_tree>\n"
        prompt
        "\n</file_tree>\n",
    )}],
)

print(response)