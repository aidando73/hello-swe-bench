import json

with open('sample_row.json', 'r') as f:
    sample_row = json.load(f)

print('\033[95m' + "Gold standard patch:" + '\033[0m')
print(sample_row['patch'])