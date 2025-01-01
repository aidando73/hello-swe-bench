import os

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

# Filter to only include top-level files and directories
top_level = set()

for line in file_tree.splitlines():
    # Sometimes git ls-tree returns lines with quotes around them. E.g., if there are spaces in the file name.
    line = line.strip("\"")
    if "/" in line:
        top_level.add(line.split("/")[0] + "/")
    else:
        top_level.add(line)

# Sort directories first by checking if item ends with "/"
top_level = sorted(top_level, key=lambda x: (not x.endswith("/"), x))

print("\n".join(top_level))
