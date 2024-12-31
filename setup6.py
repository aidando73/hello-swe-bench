from datasets import load_dataset
import os

swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
df = swebench.to_pandas()

# Filter out only django instances
df_django = df[df['repo'] == 'django/django']

# Only version 5.x instances
df_django = df_django[df_django['version'].str.contains('5.') | df_django['version'].str.contains('4.')].reset_index(drop=True)

# Read current instance index
with open('current_instance.txt', 'r') as f:
    instance_idx, instance_id = f.read().strip().split(',')
    instance_idx = int(instance_idx)

sample_row = df_django.iloc[instance_idx]


# Increment instance index
instance_idx = (instance_idx + 1) % len(df_django)

# Write new instance
with open('current_instance.txt', 'w') as f:
    f.write(f"{instance_idx},{sample_row['instance_id']}")

print(f"Setting up instance: {sample_row['instance_id']}, instance_idx: {instance_idx}, version: {sample_row['version']}")

import json

with open('sample_row.json', 'w') as f:
    json.dump(sample_row.to_dict(), f)

commit = sample_row['base_commit']

print(f"Checking out commit {commit}")
os.system(f"cd {SCRIPT_DIR}/django && git checkout -f {commit}")
