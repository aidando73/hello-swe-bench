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
if os.path.exists('current_instance.txt'):
    with open('current_instance.txt', 'r') as f:
        instance_id = f.read().strip()
else:
    instance_id = df_django.iloc[0]['instance_id']


sample_row = df_django[df_django['instance_id'] == instance_id].iloc[0]

# Write new instance
# with open('current_instance.txt', 'w') as f:
#     current_idx = df_django[df_django['instance_id'] == instance_id].index[0]
#     next_idx = (current_idx + 1) % len(df_django)
#     next_instance_id = df_django.iloc[next_idx]['instance_id']
#     f.write(next_instance_id)

print(f"Setting up instance: {sample_row['instance_id']}, version: {sample_row['version']}")

import json

with open('sample_row.json', 'w') as f:
    json.dump(sample_row.to_dict(), f)

commit = sample_row['base_commit']

print(f"Checking out commit {commit}")
os.system(f"cd {SCRIPT_DIR}/django && git checkout -f {commit}")
