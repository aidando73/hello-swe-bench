import json
import os
from llama_stack_client import LlamaStackClient
from llama_models.llama3.api.chat_format import ChatFormat
from llama_models.llama3.api.tokenizer import Tokenizer
from llama_models.llama3.api.datatypes import StopReason
from llama_models.llama3.api.tool_utils import is_valid_python_list, parse_python_list_for_function_calls
import re

# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"

formatter = ChatFormat(Tokenizer.get_instance())

if "3.2" in MODEL_ID or "3.3" in MODEL_ID:
    tool_prompt_format = "python_list"
else:
    tool_prompt_format = "json"

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

with open("problem_statement.txt", "r") as f:
    problem_statement = f.read()

with open("sample_row.json", "r") as f:
    sample_row = json.load(f)

problem_statement = sample_row["problem_statement"]

# We don't add <|begin_of_text|> because fireworks 
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
                    "description": "Absolute path to file or directory, e.g. `/Users/aidand/dev/django/file.py` or `/Users/aidand/dev/django`."
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
                    "description": "The absolute path to the file to view, e.g. `/Users/aidand/dev/django/file.py` or `/Users/aidand/dev/django`."
                }
            }
        }
    }
]

Please explain your reasoning before you make any edits in a <thinking> tag.<|eot_id|><|start_header_id|>user<|end_header_id|>

<working_directory>
%working_directory%
</working_directory>

<repository>
%file_tree%
</repository>

<problem_statement>
%problem_statement%
</problem_statement>

Please start by viewing files in the repository to understand the problem.<|eot_id|>
""".lstrip()


message = message.replace("%working_directory%", os.getcwd() + "/django")
message = message.replace("%file_tree%", file_tree)
message = message.replace("%problem_statement%", problem_statement)

def parse_tool_calls(content):
    tool_calls = []
    for match in re.finditer(r'<tool>(.*?)</tool>', content, re.DOTALL):
        tool_content = match.group(1)
        if not is_valid_python_list(tool_content):
            # Sometimes Llama returns a tool call without the list
            tool_content = f"[{tool_content}]"

        if is_valid_python_list(tool_content):
            result = parse_python_list_for_function_calls(tool_content)
            tool_calls.extend(result)
        else:
            print("Not valid tool call: ", tool_content)
    return tool_calls


ITERATIONS = 5

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

for i in range(ITERATIONS):
    message += "<|start_header_id|>assistant<|end_header_id|>\n\n"
    response = client.inference.completion(
        model_id=MODEL_ID,
        content=message,
    )
    thinking_match = re.search(r'<thinking>(.*?)</thinking>', response.content, re.DOTALL)
    if thinking_match:
        print("\033[94mThinking:", thinking_match.group(1).strip(), "\033[0m")

    message += response.content
    message += f"<|eot_id|>"

    # Parse tool tags from response
    tool_calls = parse_tool_calls(response.content)
    for tool_name, tool_params in tool_calls:
        print(f"\033[92mCalling tool: {tool_name}({tool_params})\033[0m")

    if not tool_calls and not thinking_match:
        print(f"\033[94mThinking: {response.content}\033[0m")


with open("message.txt", "w") as f:
    f.write(message)
# print(formatter.decode_assistant_message_from_content(message.content, StopReason.end_of_turn))
