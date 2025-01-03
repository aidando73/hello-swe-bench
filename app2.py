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

with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()

response = completion(
    model=model,
    messages=[{"role": "user", "content": (
        "<file_tree>\n" +
        prompt +
        "\n</file_tree>\n" +
        "<problem_statement>\n" +
        problem_statement +
        "\n</problem_statement>\n" +
        "You are a staff level software engineer.\n" +
        "Please help me locate potential files in <file_tree> that contains the code that needs to be changed to fix the <problem_statement>.\n"
        # This makes the model consistently return file names (through not in xml tags)
        "Please return file names in the format of <file_names> separated by commas.\n"
        # This reduces the number of files returned:
        # "For example, if the file names are 'app.py' and 'main.py', please return '<file_names>app.py,main.py</file_names>'.\n"
    )}],
)

content = response['choices'][0]['message']['content']
file_names = content.split(',')
for file_name in file_names:
    print(file_name.strip())
# print(response['choices'][0]['message']['content'])
