with open("runtime/src/vm.py", "r") as f:
    content = f.read()

content = content.replace('c="श्वेत"', 'c="white"')
content = content.replace('c="कृष्ण"', 'c="black"')

with open("runtime/src/vm.py", "w") as f:
    f.write(content)
