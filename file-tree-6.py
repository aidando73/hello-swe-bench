from file_tree_5 import list_files
import sys

depth = int(sys.argv[1])

print(list_files("/workspace/django", depth=depth))
