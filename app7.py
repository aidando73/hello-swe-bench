from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)
import json
import os

model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"
# model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"
# model = "anthropic/claude-3-5-sonnet-20240620"

# git ls-tree -r --name-only HEAD

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()

with open('sample_row.json', 'r') as f:
    sample_row = json.load(f)

problem_statement = sample_row['problem_statement']

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

history = []

response = completion(
    model=model,
    messages=[{"role": "user", "content": (
        "<history>\n" +
        "\n".join(history) +
        "\n</history>\n" +
        "<repository>\n" +
        file_tree +
        "\n</repository>\n" +
        "<problem_statement>\n" +
        problem_statement +
        "\n</problem_statement>\n" +
        "You are an expert software engineer.\n" +
        "You are given a file tree and a problem statement. Please fix the problem.\n" +
        "The history of your previous actions is included in <history>.\n" +
        "Please start by using the str_replace_editor `view` tool to view relevant files in the repository.\n" +
        "Then use the str_replace_editor `str_replace` tool to edit the files.\n"
        # "You will be given a tool to run commands in the repository.\n" +
        # "You will be given a tool to view the repository.\n" +
        # "You will be given a tool to view the git diff of the repository.\n" +
        # "You will be given a tool to view the git log of the repository.\n" +
        # "You will be given a tool to view the git status of the repository.\n" +
        # "You will be given a tool to view the git branch of the repository.\n" +
        # "You will be given a tool to view the git commit of the repository.\n" +
    )}],
    tools=[StrReplaceEditorTool],
)

message = response['choices'][0]['message']
if message.get('tool_calls') != None:
    function = message['tool_calls'][0]['function']
    try:
        arguments = json.loads(function['arguments'])
        print('\033[94m' + function['name'], json.dumps(arguments, indent=2) + '\033[0m')
        history_item = f"{function['name']}: {json.dumps(arguments, indent=2)}"
        if arguments['command'] == 'str_replace':
            try:
                with open(f"django/{arguments['path']}", 'w') as f:
                    old_str = arguments['old_str']
                    new_str = arguments['new_str']
                    f.write(f.read().replace(old_str, new_str))
            except FileNotFoundError:
                print(f"File {arguments['path']} not found. Skipping...")
                history_item += f"Result: Error - File {arguments['path']} not found."
        elif arguments['command'] == 'insert':
            try:
                with open(f"django/{arguments['path']}", 'w') as f:
                    line_number = arguments['insert_line']
                    lines = f.readlines()
                    lines.insert(line_number, arguments['new_str'])
                    f.writelines(lines)
            except FileNotFoundError:
                print(f"File {arguments['path']} not found. Skipping...")
                history_item += f"Result: Error - File {arguments['path']} not found."
        elif arguments['command'] == 'view':
            try:
                with open(f"django/{arguments['path']}", 'r') as f:
                    file_content = f.read()
                    history_item += f"Result: {file_content}"
            except FileNotFoundError:
                print(f"File {arguments['path']} not found. Skipping...")
                history_item += f"Result: Error - File {arguments['path']} not found."
        elif arguments["command"] == "create":
            try:
                with open(f"django/{arguments['path']}", 'w') as f:
                    f.write(arguments['file_text'])
            except FileNotFoundError:
                print(f"File {arguments['path']} not found. Skipping...")
                history_item += f"Result: Error - File {arguments['path']} not found."
        history.append(history_item)
    except json.JSONDecodeError:
        print('\033[91mInvalid JSON in tool call arguments.\033[0m')
        history_item += f"Result: Error - Invalid JSON in tool call arguments: {function['arguments']}"
    except Exception as e:
        print(f"Error - skipping: {e}")
        history_item += f"Result: Error - {e}"

else:
    print('\033[93mNo tool calls found in the response.\033[0m')
    print(message['content'])
print(f"Input tokens: {response['usage']['prompt_tokens']}", f"Output tokens: {response['usage']['completion_tokens']}")
