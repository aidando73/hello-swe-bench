from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)

# model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"
model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"
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

# Write chunks to separate files for debugging
for i, chunk in enumerate(tree_chunks):
    with open(f'tree_chunk_{i+1}.txt', 'w') as f:
        f.write(chunk)


with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()

import json
# Open and read sample_row.json
with open('sample_row.json', 'r') as f:
    sample_row = json.load(f)

potential_files = []
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
            potential_files.append(file_name.strip())
    else:
        print('\033[91mNo file names found in the response.\033[0m')
    print(f"Input tokens: {response['usage']['prompt_tokens']}")
    print(f"Output tokens: {response['usage']['completion_tokens']}")
    # print(response['choices'][0]['message']['content'])


with open('potential_files.txt', 'w') as f:
    for file in potential_files:
        f.write(file + '\n')


_STR_REPLACE_EDITOR_DESCRIPTION = """Custom editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`

Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. Be mindful of whitespaces!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`
"""

StrReplaceEditorTool = ChatCompletionToolParam(
    type='function',
    function=ChatCompletionToolParamFunctionChunk(
        name='str_replace_editor',
        description=_STR_REPLACE_EDITOR_DESCRIPTION,
        parameters={
            'type': 'object',
            'properties': {
                'command': {
                    'description': 'The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.',
                    'enum': ['view', 'create', 'str_replace', 'insert', 'undo_edit'],
                    'type': 'string',
                },
                'path': {
                    'description': 'Absolute path to file or directory, e.g. `/workspace/file.py` or `/workspace`.',
                    'type': 'string',
                },
                'file_text': {
                    'description': 'Required parameter of `create` command, with the content of the file to be created.',
                    'type': 'string',
                },
                'old_str': {
                    'description': 'Required parameter of `str_replace` command containing the string in `path` to replace.',
                    'type': 'string',
                },
                'new_str': {
                    'description': 'Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.',
                    'type': 'string',
                },
                'insert_line': {
                    'description': 'Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.',
                    'type': 'integer',
                },
                'view_range': {
                    'description': 'Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.',
                    'items': {'type': 'integer'},
                    'type': 'array',
                },
            },
            'required': ['command', 'path'],
        },
    ),
)


# for file_name in potential_files:

#     try:
#         file_content = ""
#         with open(f"django/{file_name}", 'r') as f:
#             file_content = f.read()
#     except FileNotFoundError:
#         print(f"File {file_name} not found. Skipping...")
#         continue

#     response = completion(
#         model=model,
#         messages=[{"role": "user", "content": (
#             "<file_name>\n" +
#             file_name +
#             "\n</file_name>\n" +
#             "<file_content>\n" +
#             file_content +
#             "\n</file_content>\n" +
#             "<problem_statement>\n" +
#             problem_statement +
#             "\n</problem_statement>\n" +
#             "You are a staff level software engineer.\n" +
#             "Another engineer has read the same problem statement and has identified the file <file_name> as a potential candidate for fixing the problem statement.\n"
#             "The file content is included in <file_content>.\n"
#             "Please determine if the file <file_name> contains the code that needs to be changed to fix the <problem_statement>.\n"
#             "If it does please use the `str_replace` tool to edit the file.\n"
#             "If it does not, please return <no_code_to_change>.\n"
#         )}],
#         tools=[StrReplaceEditorTool],
#     )

#     # print(response)
#     content = response['choices'][0]['message']
#     if 'tool_calls' in content:
#         function = content['tool_calls'][0]['function']
#         print(function['name'], function['arguments'])
#     else:
#         print(content['content'])
