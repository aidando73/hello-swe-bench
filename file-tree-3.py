import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

def list_files(path, depth=1):
    if path.startswith("/workspace/"):
        path = os.path.join(SCRIPTS_DIR, path[len("/workspace/") :])
    else:
        # If it doesn't start with /workspace, we'll assume it's a relative path
        path = os.path.join(SCRIPTS_DIR, path)
    
    # Check if path exists
    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} does not exist")
    
    if os.path.isfile(path):
        return [path]

    files = os.popen(f"cd {path} && git ls-tree -r --name-only HEAD").read()
    top_level = set()
    for line in files.splitlines():
        # Sometimes git ls-tree returns lines with quotes around them. E.g., if there are spaces in the file name.
        line = line.strip("\"")
        parts = line.split("/")
        if len(parts) >= depth:
            for i in range(min(depth, len(parts))):
                file_name = "/".join(parts[:i+1])
                # Add trailing slash for directories
                if i < len(parts) - 1:  # Not the full path, so must be a directory
                    file_name += "/"
                elif i == len(parts) - 1 and line.endswith("/"):
                    file_name += "/"
                top_level.add(file_name)
    # Sort directories first by checking if item ends with "/"
    return  sorted(top_level, key=lambda x: (not x.endswith("/"), x))

print("\n".join(list_files("/workspace/django", depth=2)))
