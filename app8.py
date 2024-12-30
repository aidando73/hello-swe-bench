from litellm import completion
from litellm import (
    ChatCompletionToolParam,
    ChatCompletionToolParamFunctionChunk,
    ModelResponse,
)
import json
import os

# model = "fireworks_ai/accounts/fireworks/models/llama-v3p3-70b-instruct"
# model = "fireworks_ai/accounts/fireworks/models/llama-v3p1-405b-instruct"
model = "anthropic/claude-3-5-sonnet-20240620"

# git ls-tree -r --name-only HEAD

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

with open("problem_statement.txt", "r") as f:
    problem_statement = f.read()

with open("sample_row.json", "r") as f:
    sample_row = json.load(f)

problem_statement = sample_row["problem_statement"]

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

ITERATIONS = 5

messages = [
    {
        "role": "user",
        "content": (
            "<repository>\n"
            + file_tree
            + "\n</repository>\n"
            + "<problem_statement>\n"
            + problem_statement
            + "\n</problem_statement>\n"
            + "You are an expert software engineer.\n"
            + "You are given a file tree and a problem statement. Please fix the problem.\n"
            + "You have the str_replace_editor tool to view, create, edit and undo files in the repository.\n"
            # "Please include the <done> tag in your response when you are finished.\n"
            # "You will be given a tool to run commands in the repository.\n" +
            # "You will be given a tool to view the repository.\n" +
            # "You will be given a tool to view the git diff of the repository.\n" +
            # "You will be given a tool to view the git log of the repository.\n" +
            # "You will be given a tool to view the git status of the repository.\n" +
            # "You will be given a tool to view the git branch of the repository.\n" +
            # "You will be given a tool to view the git commit of the repository.\n" +
        ),
    }
]

for i in range(ITERATIONS):
    response = completion(
        model=model,
        messages=messages,
        tools=[StrReplaceEditorTool],
    )

    message = response["choices"][0]["message"]
    # print(message)
    messages.append(message)
    if message.get("tool_calls") != None:
        function = message["tool_calls"][0]["function"]
        id = message["tool_calls"][0]["id"]
    else:
        # Try to parse the response as a tool call
        # In some cases, the response is not a tool call, but in the response
        try:
            function = json.loads(message["content"])
            if (
                function["type"] != "function"
                or function["name"] != "str_replace_editor"
            ):
                function = None
            else:
                function = {
                    "name": function["name"],
                    "arguments": json.dumps(function["parameters"]),
                }
                import uuid
                id = uuid.uuid4()
        except json.JSONDecodeError:
            function = None
        except Exception as e:
            print(f"Could not parse tool call: {e}")
            import traceback

            print(f"Could not parse tool call: {e}")
            print("Stacktrace:")
            print(traceback.format_exc())

            function = None

    if function:
        try:
            if "content" in message and message["content"] != None:
                print("\033[95m" + message["content"] + "\033[0m")
            arguments = json.loads(function["arguments"])
            print(
                "\033[94m" + function["name"],
                json.dumps(arguments, indent=2) + "\033[0m",
            )
            if arguments["command"] == "str_replace":
                try:
                    with open(f"django/{arguments['path']}", "w") as f:
                        old_str = arguments["old_str"]
                        new_str = arguments["new_str"]
                        f.write(f.read().replace(old_str, new_str))
                        messages.append(
                            {
                                "role": "tool",
                                "name": function["name"],
                                "tool_call_id": id,
                                "content": f"Result: {f.read()}",
                            }
                        )
                except FileNotFoundError:
                    print(f"File {arguments['path']} not found. Skipping...")
            elif arguments["command"] == "insert":
                try:
                    with open(f"django/{arguments['path']}", "w") as f:
                        line_number = arguments["insert_line"]
                        lines = f.readlines()
                        lines.insert(line_number, arguments["new_str"])
                        f.writelines(lines)
                        messages.append(
                            {
                                "role": "tool",
                                "name": function["name"],
                                "tool_call_id": id,
                                "content": f"Result: {f.read()}",
                            }
                        )
                except FileNotFoundError:
                    print(f"File {arguments['path']} not found. Skipping...")
                    messages.append(
                        {
                            "role": "tool",
                            "name": function["name"],
                            "tool_call_id": id,
                            "content": f"Result: Error - File {arguments['path']} not found.",
                        }
                    )
            elif arguments["command"] == "view":
                try:
                    with open(f"django/{arguments['path']}", "r") as f:
                        file_content = f.read()
                        messages.append(
                            {
                                "role": "tool",
                                "name": function["name"],
                                "tool_call_id": id,
                                "content": f"Result: {file_content}",
                            }
                        )
                except FileNotFoundError:
                    print(f"File {arguments['path']} not found. Skipping...")
                    messages.append(
                        {
                            "role": "tool",
                            "name": function["name"],
                            "tool_call_id": id,
                            "content": f"Result: Error - File {arguments['path']} not found.",
                        }
                    )
            elif arguments["command"] == "create":
                try:
                    with open(f"django/{arguments['path']}", "w") as f:
                        f.write(arguments["file_text"])
                        messages.append(
                            {
                                "role": "tool",
                                "name": function["name"],
                                "tool_call_id": id,
                                "content": f"Result: {f.read()}",
                            }
                        )
                except FileNotFoundError:
                    print(f"File {arguments['path']} not found. Skipping...")
                    messages.append(
                        {
                            "role": "tool",
                            "name": function["name"],
                            "tool_call_id": id,
                            "content": f"Result: Error - File {arguments['path']} not found.",
                        }
                    )
        except json.JSONDecodeError:
            print("\033[91mInvalid JSON in tool call arguments.\033[0m")
            messages.append(
                {
                    "role": "tool",
                    "name": function["name"],
                    "tool_call_id": id,
                    "content": f"Result: Error - Invalid JSON in tool call arguments: {function['arguments']}",
                }
            )
        except Exception as e:
            print(f"Error - skipping: {e}")
            import traceback
            print("\033[91m" + "".join(traceback.format_exc()) + "\033[0m")
            messages.append(
                {
                    "role": "tool",
                    "name": function["name"],
                    "tool_call_id": id,
                    "content": f"Result: Error - {e}",
                }
            )

    else:
        print(message["content"])
        # if "<done>" in message["content"]:
        #     break
    print(
        f"Input tokens: {response['usage']['prompt_tokens']}",
        f"Output tokens: {response['usage']['completion_tokens']}",
    )
    if "anthropic" in model:
        import time
        time.sleep(60)

# print("Loop finished")
with open("messages.json", "w") as f:
    json.dump([message.model_dump() if hasattr(message, 'model_dump') else message for message in messages], f, indent=2)