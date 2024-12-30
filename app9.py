from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)
import json
import os
import copy
import re
from fn_call_converter import convert_non_fncall_messages_to_fncall_messages, convert_tools_to_description

# model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"
model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"


SYSTEM_PROMPT_SUFFIX_TEMPLATE = """
You are an agent that can interact with a computer to solve software engineering tasks.

You have access to the following functions:

{description}

If you choose to call a function ONLY reply in the following format with NO suffix:

<function=example_function_name>
<parameter=example_parameter_1>value_1</parameter>
<parameter=example_parameter_2>
This is the value for the second parameter
that can span
multiple lines
</parameter>
</function>

<IMPORTANT>
Reminder:
- Function calls MUST follow the specified format, start with <function= and end with </function>
- Required parameters MUST be specified
- Only call one function at a time
- You may provide optional reasoning for your function call in natural language BEFORE the function call, but NOT after.
- If there is no function call available, answer the question like normal with your current knowledge and do not tell the user about function calls
"""

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
    type="function",
    function=ChatCompletionToolParamFunctionChunk(
        name="str_replace_editor",
        description=_STR_REPLACE_EDITOR_DESCRIPTION,
        parameters={
            "type": "object",
            "properties": {
                "command": {
                    "description": "The commands to run. Allowed options are: `view`, `create`, `str_replace`, `insert`, `undo_edit`.",
                    "enum": ["view", "create", "str_replace", "insert", "undo_edit"],
                    "type": "string",
                },
                "path": {
                    "description": "Absolute path to file or directory, e.g. `/workspace/file.py` or `/workspace`.",
                    "type": "string",
                },
                "file_text": {
                    "description": "Required parameter of `create` command, with the content of the file to be created.",
                    "type": "string",
                },
                "old_str": {
                    "description": "Required parameter of `str_replace` command containing the string in `path` to replace.",
                    "type": "string",
                },
                "new_str": {
                    "description": "Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert.",
                    "type": "string",
                },
                "insert_line": {
                    "description": "Required parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`.",
                    "type": "integer",
                },
                "view_range": {
                    "description": "Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
                    "items": {"type": "integer"},
                    "type": "array",
                },
            },
            "required": ["command", "path"],
        },
    ),
)

system_prompt = SYSTEM_PROMPT_SUFFIX_TEMPLATE.format(description=convert_tools_to_description([StrReplaceEditorTool]))

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

with open("problem_statement.txt", "r") as f:
    problem_statement = f.read()

with open("sample_row.json", "r") as f:
    sample_row = json.load(f)

problem_statement = sample_row["problem_statement"]

ITERATIONS = 5

messages = [
    {
        "role": "system",
        "content": system_prompt,
    },
    {
        "role": "user",
        "content": (
            "<repository>\n"
            + file_tree
            + "\n</repository>\n"
            + "<problem_statement>\n"
            + problem_statement
            + "\n</problem_statement>\n"
            + "You are given a file tree in <repository> and a problem statement in <problem_statement>. Please fix the problem.\n"
            # "Please include the <done> tag in your response when you are finished.\n"
            # "You will be given a tool to run commands in the repository.\n" +
            # "You will be given a tool to view the repository.\n" +
            # "You will be given a tool to view the git diff of the repository.\n" +
        ),
    }
]


for i in range(ITERATIONS):
    response = completion(
        model=model,
        messages=messages,
    )

    message = response["choices"][0]["message"]

    messages.append(message)
    try:
        messages = convert_non_fncall_messages_to_fncall_messages(messages, [StrReplaceEditorTool])
    except Exception as e:
        messages.append({
            "role": "tool_call",
            "content": str(e),
        })

    print("\033[94m" + message["content"] + "\033[0m")


res = []
for message in messages:
    if hasattr(message, "model_dump"):
        res.append(message.model_dump())
    else:
        res.append(message)


with open(f"messages.json", "w") as f:
    json.dump(res, f, indent=2)
