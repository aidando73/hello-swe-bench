
import re

# content = "Here 1<tool>test</tool>Here 2<tool>test2</tool>Here 3"
# print(re.sub(r'<tool>.*?</tool>', '', content, flags=re.DOTALL).strip())

# content = '<tool>view_file(path="/workspace/django/tests/admin_inlines/test_templates.py")</tool>'
# for match in re.finditer(r'<tool>(.*?)</tool>', content, re.DOTALL):
#     print(match.group(1))


content = 'testing<tool>view_file(path="/workspace/django/tests/admin_inlines/test_templates.py")</tool>testing'
for match in re.finditer(r'<tool>(.*?)</tool>', content, re.DOTALL):
    print(match.group(0))