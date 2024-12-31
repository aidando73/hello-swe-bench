import json
import os
import re
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPT_DIR, 'sample_row.json'), 'r') as f:
    sample_row = json.load(f)

with open(os.path.join(SCRIPT_DIR, 'django/test.patch'), 'w') as f:
    f.write(sample_row["test_patch"])

# print(json.dumps(sample_row, indent=4))

# print(sample_row["base_commit"])

print("Applying patch...")
os.system(f"cd {SCRIPT_DIR}/django && git apply test.patch")
print('\033[92mPatch applied\033[0m')

if sample_row["version"] == "4.0":
    environment = "env_3_8"
elif sample_row["version"] in ["4.1", "4.2"]:
    environment = "env_3_9"
elif sample_row["version"] == "5.0":
    environment = "env_3_11"
else:
    raise ValueError(f"Unknown version: {sample_row['version']}")


diff_pat = r"diff --git a/.* b/(.*)"
test_patch = sample_row['test_patch']
directives = re.findall(diff_pat, test_patch)

directives_transformed = []
for d in directives:
    d = d[: -len(".py")] if d.endswith(".py") else d
    d = d[len("tests/") :] if d.startswith("tests/") else d
    d = d.replace("/", ".")
    directives_transformed.append(d)
directives = directives_transformed

print('\033[94m' + f"Running command: ./tests/runtests.py --settings=test_sqlite --parallel 1 {' '.join(directives)}" + '\033[0m')

os.system(
    f"cd {SCRIPT_DIR}/django && "
    f"source ~/miniconda3/bin/activate && "
    f"conda activate {environment} && "
    f"python -m pip install -e ."
)

test_result =os.system(
    f"cd {SCRIPT_DIR}/django && "
    f"./tests/runtests.py --settings=test_sqlite --parallel 1 {' '.join(directives)}"
)

if test_result == 0:
    print('\033[92mTest passed\033[0m')
else:
    print('\033[91mTest failed\033[0m')

print("Reverting patch...")
# os.system(f"cd {SCRIPT_DIR}/django && git apply -R test.patch")
# print('\033[92mPatch reverted\033[0m')

