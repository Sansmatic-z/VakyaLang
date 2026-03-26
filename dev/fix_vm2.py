import re

with open('runtime/src/vm.py', 'r') as f:
    content = f.read()

# I will find the keys and reorder them.
# The problematic insertions:
#             'जेसन_पढ़ो': _json_decode,
#             'पायथन_आयात': पायथन_आयात,
#             'पायथन_चलाओ': पायथन_चलाओ,
#             'पायथन_मूल्यांकन': पायथन_मूल्यांकन,

content = content.replace(
    "'जेसन_पढ़ो': _json_decode,\n            'पायथन_आयात': पायथन_आयात,\n            'पायथन_चलाओ': पायथन_चलाओ,\n            'पायथन_मूल्यांकन': पायथन_मूल्यांकन,",
    "'जेसन_पढ़ो': _json_decode,"
)

# Insert at the end of the return block (before })
content = content.replace(
    "'_chitra_pixel_set': lambda *args: _chitra_pixel_set_impl(*args),\n        }",
    "'_chitra_pixel_set': lambda *args: _chitra_pixel_set_impl(*args),\n            'पायथन_आयात': पायथन_आयात,\n            'पायथन_चलाओ': पायथन_चलाओ,\n            'पायथन_मूल्यांकन': पायथन_मूल्यांकन,\n        }"
)

with open('runtime/src/vm.py', 'w') as f:
    f.write(content)
print("Fixed vm.py again")
