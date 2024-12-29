from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)
import json

model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"

# Read in potential files
with open('potential_files.txt', 'r') as f:
    potential_files = [line.strip() for line in f.readlines()]

with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()


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


for file_name in potential_files:
    try:
        file_content = ""
        with open(f"django/{file_name}", 'r') as f:
            file_content = f.read()
    except FileNotFoundError:
        print(f"File {file_name} not found. Skipping...")
        continue

    response = completion(
        model=model,
        messages=[{"role": "user", "content": (
            "<file_name>\n" +
            file_name +
            "\n</file_name>\n" +
            "<file_content>\n" +
            file_content +
            "\n</file_content>\n" +
            "<problem_statement>\n" +
            problem_statement +
            "\n</problem_statement>\n" +
            "You are a staff level software engineer.\n" +
            "Another engineer has read the same problem statement and has identified the file <file_name> as a potential candidate for fixing the problem statement.\n"
            "The file content is included in <file_content>.\n"
            "Please determine if the file <file_name> contains the code that needs to be changed to fix the <problem_statement>.\n"
            "If it does please use the `str_replace` tool to edit the file.\n"
            "If it does not, please return <no_code_to_change>.\n"
        )}],
        tools=[StrReplaceEditorTool],
    )

    message = response['choices'][0]['message']
    if message.get('tool_calls') != None:
        function = message['tool_calls'][0]['function']
        print('\033[94m' + function['name'], function['arguments'] + '\033[0m')
        try:
            arguments = json.loads(function['arguments'])
            if arguments['command'] == 'str_replace':
                with open(f"django/{arguments['path']}", 'w') as f:
                    old_str = arguments['old_str']
                    new_str = arguments['new_str']
                    f.write(file_content.replace(old_str, new_str))
        except json.JSONDecodeError:
            print('\033[91mInvalid JSON in tool call arguments.\033[0m')
            continue

    else:
        print('\033[93mNo file names found in the response.\033[0m')
    print(f"Input tokens: {response['usage']['prompt_tokens']}", f"Output tokens: {response['usage']['completion_tokens']}")