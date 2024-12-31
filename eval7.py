from datasets import load_dataset
import os
import sys
swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
df = swebench.to_pandas()

if len(sys.argv) == 0:
    raise ValueError("Please provide an evaluation directory under evals/")

eval_dir = sys.argv[1]

df_django = df[df['repo'] == 'django/django']

df_django = df_django[df_django['version'].str.contains('5.') | df_django['version'].str.contains('4.')].reset_index(drop=True)

# Set initial instance index to 0
with open('current_instance.txt', 'w') as f:
    f.write(f"0,{df_django.iloc[0]['instance_id']}")

# Create eval directory and logs subdirectory if they don't exist
os.makedirs(os.path.join(eval_dir, "logs"), exist_ok=True)

for index, row in df_django.iterrows():
    instance_id = row['instance_id']
    os.system(f"python setup7.py {instance_id}")
    os.system(f"python app15.py {eval_dir}")
    os.system(f"python validate7.py {eval_dir}")