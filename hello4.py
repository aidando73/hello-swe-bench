
directory = "/Users/aidand/dev/hello-swe-bench/django"

print(f"Running in directory: {directory}")

print(f"Solving problem statement...")

with open('problem_statement.txt', 'r') as f:
    problem_statement = f.read()

print(f"Problem statement: {problem_statement}")


instruction = (
    '<uploaded_files>\n'
    f'/workspace/django\n'
    '</uploaded_files>\n'
    f"I've uploaded a python code repository in the directory /django. Consider the following PR description:\n\n"
    f'<pr_description>\n'
    f'{problem_statement}\n'
    '</pr_description>\n\n'
    'Can you help me implement the necessary changes to the repository so that the requirements specified in the <pr_description> are met?\n'
    "I've already taken care of all changes to any of the test files described in the <pr_description>. This means you DON'T have to modify the testing logic or any of the tests in any way!\n"
    'Your task is to make the minimal changes to non-tests files in the /workspace directory to ensure the <pr_description> is satisfied.\n'
    'Follow these steps to resolve the issue:\n'
    '1. As a first step, it might be a good idea to explore the repo to familiarize yourself with its structure.\n'
    '2. Create a script to reproduce the error and execute it with `python <filename.py>` using the BashTool, to confirm the error\n'
    '3. Edit the sourcecode of the repo to resolve the issue\n'
    '4. Rerun your reproduce script and confirm that the error is fixed!\n'
    '5. Think about edgecases and make sure your fix handles them as well\n'
    "Your thinking should be thorough and so it's fine if it's very long.\n"
)

print(instruction)