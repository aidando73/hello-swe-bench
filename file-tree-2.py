import os

file_tree = os.popen("cd django && git ls-tree -r --name-only HEAD").read()

# Filter to only include 2 directory levels deep
top_level = set()
for line in file_tree.splitlines():
    # Sometimes git ls-tree returns lines with quotes around them. E.g., if there are spaces in the file name.
    line = line.strip("\"")
    parts = line.split("/")
    if len(parts) >= 2:
        # Add both first and second level directories
        top_level.add(parts[0] + "/")
        top_level.add(parts[0] + "/" + parts[1] + "/")
    elif len(parts) == 1:
        # Add files in root directory
        top_level.add(parts[0])
# Sort directories first by checking if item ends with "/"
top_level = sorted(top_level, key=lambda x: (not x.endswith("/"), x))
print("\n".join(top_level))
