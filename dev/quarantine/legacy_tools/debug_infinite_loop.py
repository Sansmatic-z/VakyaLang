with open("compiler/compiler.vak", "r") as f:
    content = f.read()

# Let's add a safe guard to the while loops in compiler.vak to prevent infinite loops during compilation/execution
safe_content = content.replace("यावत् सत्य:", "चर _सुरक्षा = ०\n        यावत् सत्य और _सुरक्षा < १०००:\n            _सुरक्षा = _सुरक्षा + १")
safe_content = safe_content.replace("यावत् स्वयं.स्थिति < दीर्घता(स्वयं.स्रोत):", "चर _सुरक्षा२ = ०\n        यावत् स्वयं.स्थिति < दीर्घता(स्वयं.स्रोत) और _सुरक्षा२ < १००००:\n            _सुरक्षा२ = _सुरक्षा२ + १")

with open("compiler/compiler.vak", "w") as f:
    f.write(safe_content)
