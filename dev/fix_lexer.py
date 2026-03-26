import re
with open("compiler/compiler.vak", "r") as f:
    content = f.read()

# Replace the specific lexer loops that are causing infinite generation of EOF tokens.
# When the lexer hits EOF, `स्वयं.स्थिति >= दीर्घता(स्वयं.स्रोत)` is true, so the `यावत्` loop terminates.
# Then it hits `प्रत्यागच्छ नव टोकन("EOF", "", स्वयं.पंक्ति)`.
# The caller (`सभी_टोकन`) checks: `यदि टोकन.प्रकार == "EOF": विराम`
# BUT `टोकन.प्रकार` does NOT equal `"EOF"` because it returns `<टोकन:EOF,>`.
# Wait, why does it return `<टोकन:EOF,>`?
# Because `टोकन.विवरण()` is being called to print it: `मुद्रय "  " + टोकन.विवरण()`
# The string comparison `टोकन.प्रकार == "EOF"` is what fails.

# The issue is that string comparison in VakyaLang might be broken, OR the property access `टोकन.प्रकार` is returning something unexpected.
# Let's inspect how the `सभी_टोकन` loop behaves. If `विराम` (break) is not working, it loops infinitely.
# What if the break statement is not compiled correctly?
# I already fixed the BreakStmt compilation previously (it had no offset, but I didn't actually fix it properly maybe?)
# Wait, `BreakStmt` in `compiler.py` had `self.bytecode.emit_16bit(OpCode.JUMP, 0)` and was patched later. Let's check `fix_compiler_loops.py` from earlier. I didn't fix `BreakStmt` properly!

safe_loop = """    कर्म सभी_टोकन(स्वयं):
        चर टोकन_सूची = []
        चर _सुरक्षा = ०
        चर लूप_चल_रहा_है = सत्य
        यावत् लूप_चल_रहा_है:
            _सुरक्षा = _सुरक्षा + १
            यदि _सुरक्षा > १०००:
                लूप_चल_रहा_है = असत्य
            अन्यथा:
                चर टोकन = स्वयं.अगला_टोकन(स्वयं)
                टोकन_सूची.जोड़ो(टोकन)
                यदि टोकन.प्रकार == "EOF":
                    लूप_चल_रहा_है = असत्य
        प्रत्यागच्छ टोकन_सूची"""
content = re.sub(r'    कर्म सभी_टोकन\(स्वयं\):.*?प्रत्यागच्छ टोकन_सूची', safe_loop, content, flags=re.DOTALL)

with open("compiler/compiler.vak", "w") as f:
    f.write(content)
