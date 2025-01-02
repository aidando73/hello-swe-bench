import os

diff = os.popen("cd django && git diff").read()

print(diff)