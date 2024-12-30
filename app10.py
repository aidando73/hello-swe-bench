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

ReplaceInFileTool = {
    "tool_name": "replace_in_file",
    "description": "Replace a string in a file",
    "parameters": {
        "path": {
            "description": "Absolute path to file or directory, e.g. `/workspace/file.py` or `/workspace`.",
            "param_type": "string",
            "required": True,
        },
        "old_str": {
            "description": "The string in `path` to replace.",
            "param_type": "string",
            "required": True,
        },
        "new_str": {
            "description": "The new string to replace the old string with.",
            "param_type": "string",
            "required": True,
        },
    },
}

ViewFileTool = {
    "tool_name": "view_file",
    "description": "View a file",
    "parameters": {
        "path": {"description": "The path to the file to view.", "param_type": "string", "required": True},
    },
}

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
            + "Make sure you explain your reasoning before you use the tool.\n"
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

client = LlamaStackClient(base_url=f"http://localhost:{os.environ['LLAMA_STACK_PORT']}")

for i in range(ITERATIONS):
    print(f"\033[95mIteration {i+1}\033[0m")
    response = client.inference.chat_completion(
        model_id=MODEL_ID,
        messages=messages,
        tools=[StrReplaceEditorTool],
        tool_prompt_format=tool_prompt_format,
    )
    message = response.completion_message
    messages.append(message)
    if message.content is not None:
        print(message.content)
    else:
        print(message)

#     message = response["choices"][0]["message"]
#     # print(message)
#     messages.append(message)
#     if message.get("tool_calls") != None:
#         function = message["tool_calls"][0]["function"]
#         id = message["tool_calls"][0]["id"]
#     else:
#         # Try to parse the response as a tool call
#         # In some cases, the response is not a tool call, but in the response
#         try:
#             function = json.loads(message["content"])
#             if (
#                 function["type"] != "function"
#                 or function["name"] != "str_replace_editor"
#             ):
#                 function = None
#             else:
#                 function = {
#                     "name": function["name"],
#                     "arguments": json.dumps(function["parameters"]),
#                 }
#                 import uuid

#                 id = uuid.uuid4()
#         except json.JSONDecodeError:
#             function = None
#         except Exception as e:
#             print(f"Could not parse tool call: {e}")
#             import traceback

#             print(f"Could not parse tool call: {e}")
#             print("Stacktrace:")
#             print(traceback.format_exc())

#             function = None

#     if function:
#         try:
#             if "content" in message and message["content"] != None:
#                 print("\033[95m" + message["content"] + "\033[0m")
#             arguments = json.loads(function["arguments"])
#             print(
#                 "\033[94m" + function["name"],
#                 json.dumps(arguments, indent=2) + "\033[0m",
#             )
#             if arguments["command"] == "str_replace":
#                 try:
#                     with open(f"django/{arguments['path']}", "r") as f:
#                         file_content = f.read()
#                     with open(f"django/{arguments['path']}", "w") as f:
#                         old_str = arguments["old_str"]
#                         new_str = arguments["new_str"]
#                         new_content = file_content.replace(old_str, new_str)
#                         f.write(new_content)
#                         messages.append(
#                             {
#                                 "role": "tool",
#                                 "name": function["name"],
#                                 "tool_call_id": id,
#                                 "content": f"Result: {new_content}",
#                             }
#                         )
#                 except FileNotFoundError:
#                     print(f"File {arguments['path']} not found. Skipping...")
#             elif arguments["command"] == "insert":
#                 try:
#                     with open(f"django/{arguments['path']}", "w") as f:
#                         line_number = arguments["insert_line"]
#                         lines = f.readlines()
#                         lines.insert(line_number, arguments["new_str"])
#                         f.writelines(lines)
#                         messages.append(
#                             {
#                                 "role": "tool",
#                                 "name": function["name"],
#                                 "tool_call_id": id,
#                                 "content": f"Result: {f.read()}",
#                             }
#                         )
#                 except FileNotFoundError:
#                     print(f"File {arguments['path']} not found. Skipping...")
#                     messages.append(
#                         {
#                             "role": "tool",
#                             "name": function["name"],
#                             "tool_call_id": id,
#                             "content": f"Result: Error - File {arguments['path']} not found.",
#                         }
#                     )
#             elif arguments["command"] == "view":
#                 try:
#                     with open(f"django/{arguments['path']}", "r") as f:
#                         file_content = f.read()
#                         messages.append(
#                             {
#                                 "role": "tool",
#                                 "name": function["name"],
#                                 "tool_call_id": id,
#                                 "content": f"Result: {file_content}",
#                             }
#                         )
#                 except FileNotFoundError:
#                     print(f"File {arguments['path']} not found. Skipping...")
#                     messages.append(
#                         {
#                             "role": "tool",
#                             "name": function["name"],
#                             "tool_call_id": id,
#                             "content": f"Result: Error - File {arguments['path']} not found.",
#                         }
#                     )
#             elif arguments["command"] == "create":
#                 try:
#                     with open(f"django/{arguments['path']}", "w") as f:
#                         f.write(arguments["file_text"])
#                         messages.append(
#                             {
#                                 "role": "tool",
#                                 "name": function["name"],
#                                 "tool_call_id": id,
#                                 "content": f"Result: {f.read()}",
#                             }
#                         )
#                 except FileNotFoundError:
#                     print(f"File {arguments['path']} not found. Skipping...")
#                     messages.append(
#                         {
#                             "role": "tool",
#                             "name": function["name"],
#                             "tool_call_id": id,
#                             "content": f"Result: Error - File {arguments['path']} not found.",
#                         }
#                     )
#         except json.JSONDecodeError:
#             print("\033[91mInvalid JSON in tool call arguments.\033[0m")
#             messages.append(
#                 {
#                     "role": "tool",
#                     "name": function["name"],
#                     "tool_call_id": id,
#                     "content": f"Result: Error - Invalid JSON in tool call arguments: {function['arguments']}",
#                 }
#             )
#         except Exception as e:
#             print(f"Error - skipping: {e}")
#             import traceback

#             print("\033[91m" + "".join(traceback.format_exc()) + "\033[0m")
#             messages.append(
#                 {
#                     "role": "tool",
#                     "name": function["name"],
#                     "tool_call_id": id,
#                     "content": f"Result: Error - {e}",
#                 }
#             )

#     else:
#         print(message["content"])
#         # if "<done>" in message["content"]:
#         #     break
#     print(
#         f"Input tokens: {response['usage']['prompt_tokens']}",
#         f"Output tokens: {response['usage']['completion_tokens']}",
#     )
#     if "anthropic" in model:
#         import time

#         time.sleep(60)

# # print("Loop finished")
# with open("messages.json", "w") as f:
#     json.dump(
#         [
#             message.model_dump() if hasattr(message, "model_dump") else message
#             for message in messages
#         ],
#         f,
#         indent=2,
#     )
