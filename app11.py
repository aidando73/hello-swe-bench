import json
import os
from llama_stack_client import LlamaStackClient

# MODEL_ID = "meta-llama/Llama-3.1-405B-Instruct-FP8"
MODEL_ID = "meta-llama/Llama-3.3-70B-Instruct"
# model = "anthropic/claude-3-5-sonnet-20240620"

# git ls-tree -r --name-only HEAD

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

message = """
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert software engineer.
You will be given a file tree in <file_tree> and a problem statement in <problem_statement>.

Based on the <problem_statement>, you will need to make one or more function/tool calls to achieve the purpose.
If none of the function can be used, point it out. If the given question lacks the parameters required by the function,
also point it out. You should only return the function call in tools call sections.

If you decide to invoke any of the function(s), you MUST put it in the format of <tool>[func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]</tool>

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
]<|eot_id|><|start_header_id|>user<|end_header_id|>

<working_directory>
{working_directory}
</working_directory>

<repository>
{file_tree}
</repository>

<problem_statement>
{problem_statement}
</problem_statement>

Please start by viewing files in the repository to understand the problem.
Please explain your reasoning before you make any edits in a <thinking> tag.<|eot_id|>
""".lstrip()


# message = message.format(
#     # working_directory=os.getcwd() + "/django",
#     # file_tree=file_tree,
#     # problem_statement=problem_statement,
# )

ITERATIONS = 5

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

response = client.inference.completion(
    model_id=MODEL_ID,
    content=message,
)
message = response
print(message)