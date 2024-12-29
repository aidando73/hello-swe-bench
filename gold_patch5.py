import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(SCRIPT_DIR, 'sample_row.json'), 'r') as f:
    sample_row = json.load(f)

patch = sample_row['patch']
with open(os.path.join(SCRIPT_DIR, 'gold.patch'), 'w') as f:
    f.write(patch)