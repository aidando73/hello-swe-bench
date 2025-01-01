from datasets import load_dataset
import os
import sys
swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
df = swebench.to_pandas()

if len(sys.argv) == 0:
    raise ValueError("Please provide an evaluation directory under swe-evals/")

eval_dir = sys.argv[1]

# Loop through all instances
    # Checkout commit (force)
    # Run the agent
    # Add to predictions.jsonl
    # reset to original commit (unless checkout already handles changed files) - (remove all additional files)

