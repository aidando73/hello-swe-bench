import json

with open('sample_row.json', 'r') as f:
    sample_row = json.load(f)

print(sample_row['patch'])