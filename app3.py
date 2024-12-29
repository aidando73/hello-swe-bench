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

# Calculate chunk size for splitting tree output into 4 parts
chunk_size = len(tree_output) // 4
# Split tree output into 4 roughly equal chunks
tree_chunks = [
    tree_output[i:i + chunk_size] for i in range(0, len(tree_output), chunk_size)
][:4]  # Limit to 4 chunks in case of rounding

# Ensure we have exactly 4 chunks
while len(tree_chunks) < 4:
    tree_chunks.append("")

with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()


for prompt in tree_chunks:
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
            "For example, if the file names are 'src/app.py' and 'src/main.py', please return '<file_names>src/app.py,src/main.py</file_names>'.\n"
        )}],
    )

    print('\033[95mLLM call\033[0m')
    content = response['choices'][0]['message']['content']
    # file_names = content.split(',')
    # for file_name in file_names:
    #     print(file_name.strip())
    print(content)
    # Extract file names between tags and split by commas
    if '<file_names>' in content and '</file_names>' in content:
        file_names_text = content.split('<file_names>')[1].split('</file_names>')[0]
        file_names = file_names_text.split(',')
        for file_name in file_names:
            print('\033[94m' + file_name.strip() + '\033[0m')
    else:
        print('\033[91mNo file names found in the response.\033[0m')
    print(f"Input tokens: {response['usage']['prompt_tokens']}")
    print(f"Output tokens: {response['usage']['completion_tokens']}")
    # print(response['choices'][0]['message']['content'])
