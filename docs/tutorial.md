# 🎓 VakyaLang (वाक्) Tutorial

This tutorial will take you from your first "Namaste" to building persistent applications in Sanskrit.

## 1. 🕉️ Your First Program: namaste.vak

Create a new file called `namaste.vak` with the following content:
```vak
# This is a comment (टीका)
मुद्रय "नमस्ते जगत्!"
```
**Run it:**
```bash
python vak.py run namaste.vak
```

## 2. चर (Variables)
Use `चर` (cara) to declare a variable. Vāk supports both ASCII and Devanagari numerals.
```vak
चर नाम = "राज"
चर आयु = २१
मुद्रय नाम + " की आयु " + पाठ_कर(आयु) + " है।"
```

## 3. कर्म (Functions)
Functions are defined using the `कर्म` (karma) keyword. They support parameters and return values.
```vak
कर्म योगफल(क, ख):
    प्रत्यागच्छ क + ख

मुद्रय "५ + ७ =", योगफल(५, ७)
```

## 4. वर्ग (Classes)
Vāk is fully object-oriented. Use `वर्ग` (varga) for class definitions.
```vak
वर्ग पशु:
    कर्म प्रारम्भ(स्वयं, नाम):
        स्वयं.नाम = नाम

    कर्म बोलो(स्वयं):
        मुद्रय स्वयं.नाम, "बोलता है"

वर्ग कुत्ता(पशु):
    कर्म बोलो(स्वयं):
        मुद्रय स्वयं.नाम + ": भौं भौं!"

चर क = नव कुत्ता("टॉमी")
क.बोलो()
```

## 5. 📂 File Persistence
You can read and write files using the built-in system bridge.
```vak
लेखन("data.txt", "वाक् ने लिखा!")
चर सामग्री = पठन("data.txt")
मुद्रय "फ़ाइल सामग्री:", सामग्री
```

## 🧠 Next Steps
- Explore the **Examples** folder for advanced use cases (Fibonacci, Static Site Generators).
- Try the **Sanskrit Coder CLI** for mathematical calculations.
  ```bash
  python vak.py coder
  ```

---
**Architect:** Raj Mitra
