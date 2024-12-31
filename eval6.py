from datasets import load_dataset
import os

swebench = load_dataset('princeton-nlp/SWE-bench_Lite', split='test')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
df = swebench.to_pandas()

df_django = df[df['repo'] == 'django/django']

df_django = df_django[df_django['version'].str.contains('5.') | df_django['version'].str.contains('4.')].reset_index(drop=True)

# Set initial instance index to 0
with open('current_instance.txt', 'w') as f:
    f.write(f"0,{df_django.iloc[0]['instance_id']}")

for index, row in df_django.iterrows():
    os.system(f"python setup6.py")
    os.system(f"python validate6.py")