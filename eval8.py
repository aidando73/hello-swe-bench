from datasets import load_dataset
import os
import sys
import json

swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
df = swebench.to_pandas()

if len(sys.argv) == 0:
    raise ValueError("Please provide an evaluation directory under swe-evals/")

eval_dir = sys.argv[1]

# Number of instances to evaluate
NUM_INSTANCES = 1


count = 0
# Loop through all instances
for i, row in df.iterrows():
    if count >= NUM_INSTANCES:
        break
    dir = row['repo'].split('/')[1]
    commit = row['base_commit']

    # Write sample row to sample_row.json for the agent to use
    with open("sample_row.json", "w") as f:
        json.dump(row.to_dict(), f, indent=4)

    # Checkout commit (force) and clean directory
    os.system(f"cd {dir} && git checkout {commit} --force && git clean -fdx")

    # Run the agent
    os.system(f"python {SCRIPT_DIR}/run_agent.py {eval_dir}")

    # Add to predictions.jsonl
    # reset to original commit (unless checkout already handles changed files) - (remove all additional files)

