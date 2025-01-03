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
    files = files.splitlines()
    files = [f for f in files if f.count("/") < depth]
    # Sort directories first by checking if item ends with "/"
    return  sorted(files, key=lambda x: (not x.endswith("/"), x))

print("\n".join(list_files("/workspace/django", depth=2)))
