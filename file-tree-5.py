import os
from typing import List
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

class Directory:
    name: str
    files: List[str]
    directories: List['Directory']

    def __init__(self, name: str):
        self.name = name
        self.files = []
        self.directories = []
    
    def add_file(self, file: str):
        self.files.append(file)
    
    def add_directory(self, directory: 'Directory'):
        self.directories.append(directory)
    
    def __iter__(self):
        return iter(sorted(self.directories) + sorted(self.files))
    
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
    root = Directory("root")
    for file in files:
    # Sort directories first by checking if item ends with "/"
    return  sorted(files, key=lambda x: (not x.endswith("/"), x))

print("\n".join(list_files("/workspace/django", depth=2)))
