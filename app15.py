import json
import os
from llama_stack_client import LlamaStackClient
from llama_models.llama3.api.chat_format import ChatFormat
from llama_models.llama3.api.tokenizer import Tokenizer
from llama_models.llama3.api.datatypes import StopReason
from llama_models.llama3.api.tool_utils import is_valid_python_list, parse_python_list_for_function_calls
import re
import sys

# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

formatter = ChatFormat(Tokenizer.get_instance())

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

eval_dir = sys.argv[1] if len(sys.argv) > 1 else None

with open("sample_row.json", "r") as f:
    sample_row = json.load(f)

problem_statement = sample_row["problem_statement"]

message = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert software engineer.
You will be given a file tree in <file_tree> and a problem statement in <problem_statement>.

Based on the <problem_statement>, you will need to make one or more function/tool calls to achieve the purpose.
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of <tool>[func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]</tool>
If you decide to invoke multiple functions, you MUST put commas between the function calls. E.g., <tool>[func_name1(params), func_name2(params), func_name3(params)]</tool>

Here is a list of functions in JSON format that you can invoke.

[
    {
        "name": "replace_in_file",
        "description": "Replace a string in a file",
        "parameters": {
            "type": "dict",
            "required": ["path", "old_str", "new_str"],
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path to file or directory, e.g. `/workspace/django/file.py` or `/workspace/django`."
                },
                "old_str": {
                    "type": "string",
                    "description": "The string in `path` to replace."
                },
                "new_str": {
                    "type": "string",
                    "description": "The new string to replace the old string with."
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

<repository>
%file_tree%
</repository>

<problem_statement>
%problem_statement%
</problem_statement>

Please start by viewing files in the repository to understand the problem.
You are in the working directory as specified in <working_directory>. Please specify paths in absolute paths only. Relative paths will not work.<|eot_id|>
""".lstrip()


message = message.replace("%working_directory%", "/workspace/django")
message = message.replace("%file_tree%", file_tree)
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
            - tool_content (str): The original tool content
    """
    tool_calls = []
    for match in re.finditer(r'<tool>(.*?)</tool>', content, re.DOTALL):
        tool_content = match.group(1)
        if not is_valid_python_list(tool_content):
            tool_content = tool_content.strip()

            # Add square brackets if missing
            if not tool_content.startswith('['):
                tool_content = f"[{tool_content}"
            if not tool_content.endswith(']'):
                tool_content = f"{tool_content}]"
            continue

        if is_valid_python_list(tool_content):
            result = parse_python_list_for_function_calls(tool_content)
            # Add the original tool content to each result tuple
            result = [(name, params) for name, params in result]
            tool_calls.extend(result)
        else:
            print("Not valid tool call: ", match.group(1))
    return tool_calls


ITERATIONS = 5

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

finished = False

for i in range(ITERATIONS):
    if finished:
        print("\033[92mTask finished\033[0m")
        break
    message += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    response = client.inference.completion(
        model_id=MODEL_ID,
        content=message,
    )
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', response.content, re.DOTALL)
    if thinking_match:
        print("\033[94mThinking:", thinking_match.group(1).strip(), "\033[0m")
    else:
        # Check for any text outside of tool tags
        non_tool_content = re.sub(r'<tool>.*?</tool>', '', response.content, flags=re.DOTALL).strip()
        if non_tool_content:
            print(f"\033[94m{non_tool_content}\033[0m")

    message += response.content
    message += f"<|eot_id|>"

    # Parse tool tags from response
    tool_calls = parse_tool_calls(response.content)
    for tool_name, tool_params in tool_calls:
        message += f"<|start_header_id|>tool<|end_header_id|>\n\n"
        tool_call_str = f"[{tool_name}({', '.join([f'{param_name}={param_value}' for param_name, param_value in tool_params.items()])})]"
        message += f"Executed tool call: {tool_call_str}\n"
        print(f"\033[92mCalling tool: {tool_call_str}\033[0m")
        if tool_name == "replace_in_file":
            if "old_str" not in tool_params:
                print(f"\033[91mOld string not found in tool params: {tool_params}\033[0m")
                message += f"Result: Error - old_str not found in tool params. Please ensure the tool params are correct.\n"
                continue
            if "new_str" not in tool_params:
                print(f"\033[91mNew string not found in tool params: {tool_params}\033[0m")
                message += f"Result: Error - new_str not found in tool params. Please ensure the tool params are correct.\n"
                continue
            try:
                path = tool_params['path']
                if path.startswith('/workspace/'):
                    path = os.path.join(script_dir, path[len('/workspace/'):])
                else:
                    # If it doesn't start with /workspace, we'll assume it's a relative path
                    path = os.path.join(script_dir, path)
                
                with open(f"{path}", "r") as f:
                    file_content = f.read()
                with open(f"{path}", "w") as f:
                    old_str = tool_params["old_str"]
                    new_str = tool_params["new_str"]
                    new_content = file_content.replace(old_str, new_str)
                    f.write(new_content)
                message += f"Result: File successfully updated\n"
            except FileNotFoundError:
                print(f"File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists.")
                message += f"Result: Error - File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists..\n"
            except IsADirectoryError:
                print(f"Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory.")
                message += f"Result: Error - Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory..\n"
        elif tool_name == "view_file":
            try:
                path = tool_params['path']
                if path.startswith('/workspace/'):
                    path = os.path.join(script_dir, path[len('/workspace/'):])
                else:
                    # If it doesn't start with /workspace, we'll assume it's a relative path
                    path = os.path.join(script_dir, path)
                with open(f"{path}", "r") as f:
                    file_content = f.read()
                message += f"Result: {file_content}\n"
            except FileNotFoundError:
                print(f"File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists.")
                message += f"Result: Error - File {tool_params['path']} not found. Please ensure the path is an absolute path and that the file exists..\n"
            except IsADirectoryError:
                print(f"Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory.")
                message += f"Result: Error - Path {tool_params['path']} is a directory. Please ensure the path references a file, not a directory..\n"
        elif tool_name == "finish":
            finished = True
            message += f"Result: Task marked as finished\n"
        else:
            print(f"\033[91mUnknown tool: {tool_name}\033[0m")
            # TODO - does this ever fire? If so we should add into message
        message += f"<|eot_id|>"


    if not tool_calls and not thinking_match:
        print(f"\033[94mThinking: {response.content}\033[0m")


if eval_dir:
    with open(os.path.join(eval_dir, f"{sample_row['instance_id']}-prompt.txt"), "w") as f:
        f.write(message)
else:
    with open("message.txt", "w") as f:
        f.write(message)