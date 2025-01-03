import json
import os
from llama_stack_client import LlamaStackClient
from llama_models.llama3.api.chat_format import ChatFormat
from llama_models.llama3.api.tokenizer import Tokenizer
from llama_models.llama3.api.datatypes import StopReason
from llama_models.llama3.api.tool_utils import (
    is_valid_python_list,
    parse_python_list_for_function_calls,
)
import re
import sys
from file_tree_5 import list_files

# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

formatter = ChatFormat(Tokenizer.get_instance())


eval_dir = sys.argv[1] if len(sys.argv) > 1 else None

with open("sample_row.json", "r") as f:
    sample_row = json.load(f)

problem_statement = sample_row["problem_statement"]

message = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert software engineer.
You will be given a problem statement in <problem_statement>

Based on the <problem_statement>, you will need to make one or more function/tool calls to achieve the purpose.
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of <tool>[func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]</tool>
If you decide to invoke multiple functions, you MUST put commas between the function calls. E.g., <tool>[func_name1(params), func_name2(params), func_name3(params)]</tool>

Here is a list of functions in JSON format that you can invoke.

[
    {
        "name": "list_files",
        "description": "List all files in a directory.",
        "parameters": {
            "type": "dict",
            "required": ["path"],
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to a directory, e.g. `/workspace/django`. If referencing a file, will return the name of the file."
                }
            },
        }
    },
    {
        "name": "edit_file",
        "description": "Edit a file. Specify the path to the file and the new_str to write to it. If old_str is specified, only the old_str will be replaced with new_str, otherwise the entire file will be replaced by new_str.",
        "parameters": {
            "type": "dict",
            "required": ["path", "new_str"],
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to file or directory, e.g. `/workspace/django/file.py` or `/workspace/django`."
                },
                "old_str": {
                    "type": "string",
                    "description": "The string in the file at `path` to replace. If not specified, the entire file will be replaced by new_str"
                },
                "new_str": {
                    "type": "string",
                    "description": "The new string to write to the file. If the old_str is specified, only the old_str will be replaced with new_str, otherwise the entire file will be replaced by new_str."
                }
            }
        }
    },
    {
        "name": "view_file",
        "description": "View a file",
        "parameters": {
            "type": "dict",
            "required": ["path"],
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The absolute path to the file to view, e.g. `/workspace/django/file.py` or `/workspace/django`."
                }
            }
        }
    },
    {
        "name": "finish",
        "description": "If you have solved the problem, you can call this function to finish the task.",
        "parameters": {}
    }
]

Please explain your reasoning before you make any edits in a <thinking> tag.

<|eot_id|><|start_header_id|>user<|end_header_id|>

<working_directory>
%working_directory%
</working_directory>

<file_tree>
%file_tree%
</file_tree>

<problem_statement>
%problem_statement%
</problem_statement>

You are in the working directory as specified in <working_directory>. Please specify paths in absolute paths only.
I have included the top level files and directories in the repository in <file_tree>.
Please start by listing out and viewing files in the repository to understand the problem.<|eot_id|>
""".strip()


message = message.replace("%working_directory%", "/workspace/django")
message = message.replace("%file_tree%", "\n".join(list_files("/workspace/django", depth=2)))
message = message.replace("%problem_statement%", problem_statement)

script_dir = os.path.dirname(os.path.abspath(__file__))

print(f"Script dir: {script_dir}")


def parse_tool_calls(content):
    """
    Parse tool calls from the content.

    Args:
        content (str): The content to parse tool calls from.

    Returns:
        list[tuple]: A list of tuples containing:
            - name (str): The name of the tool
            - params (dict): The parameters of the tool
        or ("error", "error message") if the tool call is invalid
    """
    tool_calls = []
    for match in re.finditer(r"<tool>(.*?)</tool>", content, re.DOTALL):
        tool_content = match.group(1)
        if not is_valid_python_list(tool_content):
            tool_content = tool_content.strip()

            # Add square brackets if missing
            if not tool_content.startswith("["):
                tool_content = f"[{tool_content}"
            if not tool_content.endswith("]"):
                tool_content = f"{tool_content}]"

        try:
            result = parse_python_list_for_function_calls(tool_content)
            if is_valid_python_list(tool_content):
                # Add the original tool content to each result tuple
                result = [(name, params) for name, params in result]
                tool_calls.extend(result)
            else:
                tool_calls.append(
                    (
                        "error",
                        "Tool call invalid syntax: " + match.group(0),
                    )
                )
        except Exception as e:
            tool_calls.append(
                (
                    "error",
                    "Tool call invalid syntax: Could not parse tool call: "
                    + match.group(0)
                    + " "
                    + str(e),
                )
            )

    return tool_calls


def display_tool_params(tool_params):
    return (
        "("
        + ", ".join(
            [
                param_name + '="' + str(param_value) + '"'
                for param_name, param_value in tool_params.items()
            ]
        )
        + ")"
    )
    

ITERATIONS = 15

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

finished = False

for i in range(ITERATIONS):
    print(f"Iteration {i+1} of {ITERATIONS}")
    if finished:
        break
    message += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    response = client.inference.completion(
        model_id=MODEL_ID,
        content=message,
    )
    thinking_match = re.search(
        r"<thinking>(.*?)</thinking>", response.content, re.DOTALL
    )
    if thinking_match:
        print("\033[94mThinking:", thinking_match.group(1).strip(), "\033[0m")
    else:
        # Check for any text outside of tool tags
        non_tool_content = re.sub(
            r"<tool>.*?</tool>", "", response.content, flags=re.DOTALL
        ).strip()
        if non_tool_content:
            print(f"\033[94mThinking: {non_tool_content}\033[0m")

    message += response.content
    message += f"<|eot_id|>"

    # Parse tool tags from response
    tool_calls = parse_tool_calls(response.content)
    for tool_call in tool_calls:
        if tool_call[0] == "error":
            print(
                f"\033[91mERROR - Could not parse tool call: {tool_call[1]}\033[0m"
            )
            message += f"<|start_header_id|>tool<|end_header_id|>\n\n"
            message += (
                f"ERROR - Could not parse tool call: {tool_call[1]}"
            )
            message += f"<|eot_id|>"
            continue

        tool_name, tool_params = tool_call
        message += f"<|start_header_id|>tool<|end_header_id|>\n\n"
        tool_call_str = f"[{tool_name}{display_tool_params(tool_params)}]"
        message += f"Executing tool call: {tool_call_str}\n"
        print(f"\033[92mCalling tool: {tool_call_str}\033[0m")
        try:
            if tool_name == "list_files":
                if "path" not in tool_params:
                    print(
                        f"\033[91mResult: ERROR - path not found in tool params: {display_tool_params(tool_params)}\033[0m"
                    )
                    message += f"Result: ERROR - path not found in tool params. {display_tool_params(tool_params)}\n"
                    continue

                path = tool_params["path"]

                try: 
                    files = list_files(path, depth=1)
                    message += "Result:\n"
                    message += "\n".join(files)
                except FileNotFoundError as e:
                    print(f"\033[91mResult: ERROR - Directory not found: {e}\033[0m")
                    message += f"Result: ERROR - Directory not found: {e}\n"
            elif tool_name == "edit_file":
                if "new_str" not in tool_params:
                    print(
                        f"\033[91mnew_str not found in tool params: {display_tool_params(tool_params)}\033[0m"
                    )
                    message += f"Result: ERROR - new_str not found in tool params. {display_tool_params(tool_params)}\n"
                    continue
                try:
                    path = tool_params["path"]
                    if path.startswith("/workspace/"):
                        path = os.path.join(script_dir, path[len("/workspace/") :])
                    else:
                        # If it doesn't start with /workspace, we'll assume it's a relative path
                        path = os.path.join(script_dir, path)

                    if "old_str" in tool_params:
                        with open(f"{path}", "r") as f:
                            file_content = f.read()
                        with open(f"{path}", "w") as f:
                            old_str = tool_params["old_str"]
                            new_str = tool_params["new_str"]
                            new_content = file_content.replace(old_str, new_str)
                            f.write(new_content)
                    else:
                        with open(f"{path}", "w") as f:
                            f.write(tool_params["new_str"])
                    message += f"Result: File successfully updated\n"
                    # Get git diff for the specific file after update
                    # git_diff = os.popen(f"cd django && git diff -- {path}").read()
                    # if git_diff:
                    #     message += f"Result: File updated:\n"
                    #     message += f"{git_diff}\n"
                    # else:
                    #     message += f"Result: File unchanged\n"
                except FileNotFoundError:
                    print(
                        f"File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists."
                    )
                    message += f"Result: ERROR - File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists..\n"
                except IsADirectoryError:
                    print(
                        f"Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory."
                    )
                    message += f"Result: ERROR - Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory..\n"
            elif tool_name == "view_file":
                try:
                    path = tool_params["path"]
                    if path.startswith("/workspace/"):
                        path = os.path.join(script_dir, path[len("/workspace/") :])
                    else:
                        # If it doesn't start with /workspace, we'll assume it's a relative path
                        path = os.path.join(script_dir, path)
                    with open(f"{path}", "r") as f:
                        file_content = f.read()
                    message += f"Result: {file_content}\n"
                except FileNotFoundError:
                    print(
                        f"File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists."
                    )
                    message += f"Result: ERROR - File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists..\n"
                except IsADirectoryError:
                    print(
                        f"Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory."
                    )
                    message += f"Result: ERROR - Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory..\n"
            elif tool_name == "finish":
                finished = True
                message += f"Result: Task marked as finished\n"
            else:
                print(f"\033[91mResult: ERROR - Unknown tool: {tool_name}\033[0m")
                # TODO - does this ever fire? If so we should add into message
        except Exception as e:
            print(f"\033[91mResult: ERROR - Calling tool: {tool_name} {e}\033[0m")
            message += f"Result: ERROR - Calling tool: {tool_name} {e}\n"
        message += f"<|eot_id|>"


if finished:
    print("\033[92mAgent marked as finished\033[0m")
else:
    print("\033[91mMax iterations reached\033[0m")

if eval_dir:
    with open(
        os.path.join(eval_dir, "logs", f"{sample_row['instance_id']}-prompt.txt"), "w"
    ) as f:
        f.write(message)
else:
    with open("message.txt", "w") as f:
        f.write(message)
