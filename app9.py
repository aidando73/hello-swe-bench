from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)
import json
import os

model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"


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

def convert_tools_to_description(tools: list[dict]) -> str:
    ret = ''
    for i, tool in enumerate(tools):
        assert tool['type'] == 'function'
        fn = tool['function']
        if i > 0:
            ret += '\n'
        ret += f"---- BEGIN FUNCTION #{i+1}: {fn['name']} ----\n"
        ret += f"Description: {fn['description']}\n"

        if 'parameters' in fn:
            ret += 'Parameters:\n'
            properties = fn['parameters'].get('properties', {})
            required_params = set(fn['parameters'].get('required', []))

            for j, (param_name, param_info) in enumerate(properties.items()):
                # Indicate required/optional in parentheses with type
                is_required = param_name in required_params
                param_status = 'required' if is_required else 'optional'
                param_type = param_info.get('type', 'string')

                # Get parameter description
                desc = param_info.get('description', 'No description provided')

                # Handle enum values if present
                if 'enum' in param_info:
                    enum_values = ', '.join(f'`{v}`' for v in param_info['enum'])
                    desc += f'\nAllowed values: [{enum_values}]'

                ret += (
                    f'  ({j+1}) {param_name} ({param_type}, {param_status}): {desc}\n'
                )
        else:
            ret += 'No parameters are required for this function.\n'

        ret += f'---- END FUNCTION #{i+1} ----\n'
    return ret

def convert_non_fncall_messages_to_fncall_messages(
    messages: list[dict],
    tools: list[ChatCompletionToolParam],
) -> list[dict]:
    """Convert non-function calling messages back to function calling messages."""
    messages = copy.deepcopy(messages)
    formatted_tools = convert_tools_to_description(tools)
    system_prompt_suffix = SYSTEM_PROMPT_SUFFIX_TEMPLATE.format(
        description=formatted_tools
    )

    converted_messages = []
    tool_call_counter = 1  # Counter for tool calls

    first_user_message_encountered = False
    for message in messages:
        role, content = message['role'], message['content']
        content = content or ''  # handle cases where content is None
        # For system messages, remove the added suffix
        if role == 'system':
            if isinstance(content, str):
                # Remove the suffix if present
                content = content.split(system_prompt_suffix)[0]
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    # Remove the suffix from the last text item
                    content[-1]['text'] = content[-1]['text'].split(
                        system_prompt_suffix
                    )[0]
            converted_messages.append({'role': 'system', 'content': content})
        # Skip user messages (no conversion needed)
        elif role == 'user':
            # Check & replace in-context learning example
            if not first_user_message_encountered:
                first_user_message_encountered = True
                if isinstance(content, str):
                    content = content.replace(IN_CONTEXT_LEARNING_EXAMPLE_PREFIX, '')
                    content = content.replace(IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX, '')
                elif isinstance(content, list):
                    for item in content:
                        if item['type'] == 'text':
                            item['text'] = item['text'].replace(
                                IN_CONTEXT_LEARNING_EXAMPLE_PREFIX, ''
                            )
                            item['text'] = item['text'].replace(
                                IN_CONTEXT_LEARNING_EXAMPLE_SUFFIX, ''
                            )
                else:
                    raise FunctionCallConversionError(
                        f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                    )

            # Check for tool execution result pattern
            if isinstance(content, str):
                tool_result_match = re.search(
                    TOOL_RESULT_REGEX_PATTERN, content, re.DOTALL
                )
            elif isinstance(content, list):
                tool_result_match = next(
                    (
                        _match
                        for item in content
                        if item.get('type') == 'text'
                        and (
                            _match := re.search(
                                TOOL_RESULT_REGEX_PATTERN, item['text'], re.DOTALL
                            )
                        )
                    ),
                    None,
                )
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )

            if tool_result_match:
                if not (
                    isinstance(content, str)
                    or (
                        isinstance(content, list)
                        and len(content) == 1
                        and content[0].get('type') == 'text'
                    )
                ):
                    raise FunctionCallConversionError(
                        f'Expected str or list with one text item when tool result is present in the message. Content: {content}'
                    )
                tool_name = tool_result_match.group(1)
                tool_result = tool_result_match.group(2).strip()

                # Convert to tool message format
                converted_messages.append(
                    {
                        'role': 'tool',
                        'name': tool_name,
                        'content': [{'type': 'text', 'text': tool_result}]
                        if isinstance(content, list)
                        else tool_result,
                        'tool_call_id': f'toolu_{tool_call_counter-1:02d}',  # Use last generated ID
                    }
                )
            else:
                converted_messages.append({'role': 'user', 'content': content})

        # Handle assistant messages
        elif role == 'assistant':
            if isinstance(content, str):
                content = _fix_stopword(content)
                fn_match = re.search(FN_REGEX_PATTERN, content, re.DOTALL)
            elif isinstance(content, list):
                if content and content[-1]['type'] == 'text':
                    content[-1]['text'] = _fix_stopword(content[-1]['text'])
                    fn_match = re.search(
                        FN_REGEX_PATTERN, content[-1]['text'], re.DOTALL
                    )
                else:
                    fn_match = None
                fn_match_exists = any(
                    item.get('type') == 'text'
                    and re.search(FN_REGEX_PATTERN, item['text'], re.DOTALL)
                    for item in content
                )
                if fn_match_exists and not fn_match:
                    raise FunctionCallConversionError(
                        f'Expecting function call in the LAST index of content list. But got content={content}'
                    )
            else:
                raise FunctionCallConversionError(
                    f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                )

            if fn_match:
                fn_name = fn_match.group(1)
                fn_body = fn_match.group(2)
                matching_tool = next(
                    (
                        tool['function']
                        for tool in tools
                        if tool['type'] == 'function'
                        and tool['function']['name'] == fn_name
                    ),
                    None,
                )
                # Validate function exists in tools
                if not matching_tool:
                    raise FunctionCallValidationError(
                        f"Function '{fn_name}' not found in available tools: {[tool['function']['name'] for tool in tools if tool['type'] == 'function']}"
                    )

                # Parse parameters
                param_matches = re.finditer(FN_PARAM_REGEX_PATTERN, fn_body, re.DOTALL)
                params = _extract_and_validate_params(
                    matching_tool, param_matches, fn_name
                )

                # Create tool call with unique ID
                tool_call_id = f'toolu_{tool_call_counter:02d}'
                tool_call = {
                    'index': 1,  # always 1 because we only support **one tool call per message**
                    'id': tool_call_id,
                    'type': 'function',
                    'function': {'name': fn_name, 'arguments': json.dumps(params)},
                }
                tool_call_counter += 1  # Increment counter

                # Remove the function call part from content
                if isinstance(content, list):
                    assert content and content[-1]['type'] == 'text'
                    content[-1]['text'] = (
                        content[-1]['text'].split('<function=')[0].strip()
                    )
                elif isinstance(content, str):
                    content = content.split('<function=')[0].strip()
                else:
                    raise FunctionCallConversionError(
                        f'Unexpected content type {type(content)}. Expected str or list. Content: {content}'
                    )

                converted_messages.append(
                    {'role': 'assistant', 'content': content, 'tool_calls': [tool_call]}
                )
            else:
                # No function call, keep message as is
                converted_messages.append(message)

        else:
            raise FunctionCallConversionError(
                f'Unexpected role {role}. Expected system, user, or assistant in non-function calling messages.'
            )
    return converted_messages

class FunctionCallConversionError(Exception):
    """Exception raised when FunctionCallingConverter failed to convert a non-function call message to a function call message.

    This typically happens when there's a malformed message (e.g., missing <function=...> tags). But not due to LLM output.
    """

    def __init__(self, message):
        super().__init__(message)


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
    messages = convert_non_fncall_messages_to_fncall_messages(messages, [StrReplaceEditorTool])

    print(message)


with open(f"messages.json", "w") as f:
    json.dump([message.model_dump() for message in messages], f)