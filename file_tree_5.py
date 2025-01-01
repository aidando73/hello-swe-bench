import os
from typing import List
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

class Directory:
    name: str
    files: set[str]
    directories: set['Directory']

    def __init__(self, name: str):
        self.name = name
        self.files = set()
        self.directories = set()
    
    def add_file(self, file: str):
        self.files.add(file)
    
    def add_directory(self, directory: 'Directory'):
        self.directories.add(directory)
    
    def __str__(self):
        return f"{self.name} ({len(self.files)} files, {len(self.directories)} directories)"

    def __repr__(self):
        return f"{self.name} ({len(self.files)} files, {len(self.directories)} directories)"

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)
    
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

    root = Directory(path)
    for file in files:
        # Sometimes git ls-tree returns files with quotes around them
        # E.g., for files with spaces in their name
        file = file.strip('"')
        parts = file.split("/")
        cur = root
        for i in range(len(parts)):
            if i + 1 > depth:
                break
            if i == len(parts) - 1:
                cur.add_file(parts[i])
            else:
                if Directory(parts[i]) not in cur.directories:
                    temp = Directory(parts[i])
                    cur.add_directory(temp)
                    cur = temp
                else:
                    cur = next(d for d in cur.directories if d.name == parts[i])
    res = []
    def dfs(directory: Directory, path=""):
        # Recursively process subdirectories
        for subdir in sorted(directory.directories, key=lambda x: x.name):
            subdir_path = os.path.join(path, subdir.name)
            res.append(subdir_path + "/")  # Add trailing slash for directories
            dfs(subdir, subdir_path)
        
                # Add all files in current directory
        for file in sorted(directory.files):
            res.append(os.path.join(path, file))
    
    dfs(root)
    return  res
