# 🕉️ संस्कृत-कोडकः - पूर्णलेख्यम्

**संस्करणम् (Version):** 1.0.0  
**रचनादिनम् (Created):** March 8, 2026  
**रचयिता (Author):** Visionary RM (Raj Mitra)  
**स्थितिः (Status):** सक्रियम् (Active)

---

## 📖 परिचयः (Introduction)

संस्कृत-कोडकः एका पूर्णा संस्कृत गणित-तर्क निष्पादन तन्त्रम् अस्ति।  
अस्मिन् संस्कृतभाषायां सर्वाणि गणितीयकार्याणि कर्तुं शक्यते।

**Sanskrit Coder** is a complete Sanskrit mathematics and logic execution system.  
All mathematical operations can be performed in Sanskrit language.

---

## 🎯 उद्देशाः (Objectives)

1. **संस्कृत पुनर्जीवितम्** - Revive Sanskrit as a technical language
2. **गणितं संस्कृते** - Mathematics in Sanskrit
3. **तर्कशास्त्रं संस्कृते** - Logic in Sanskrit
4. **शिक्षणं सरलं** - Easy learning
5. **तकनीकं संस्कृते** - Technology in Sanskrit

---

## 📦 संरचना (Structure)

```
sanskrit-coder/
│
├── 📄 README.md              # मुख्यलेख्यम्
├── 📄 sanskrit_coder.md      # पूर्णलेख्यम्
├── 📄 requirements.txt       # आवश्यकताः
├── 📄 main.py                # मुख्यद्वारम्
│
├── 📁 core/                  # मुख्य भागः
│   ├── __init__.py
│   ├── engine.py             # मुख्य इन्जिन्
│   └── translator.py         # अनुवादकः
│
├── 📁 numbers/               # संख्या पद्धतिः
│   ├── __init__.py
│   └── sanskrit_numbers.py   # संख्या तन्त्रम्
│
├── 📁 grammar/               # व्याकरणम्
│   ├── __init__.py
│   └── grammar.py            # व्याकरण इन्जिन्
│
├── 📁 math_engine/           # गणित इन्जिन्
│   ├── __init__.py
│   └── math_engine.py        # गणित तन्त्रम्
│
├── 📁 logic_engine/          # तर्क इन्जिन्
│   ├── __init__.py
│   └── logic_engine.py       # तर्क तन्त्रम्
│
└── 📁 tests/                 # परीक्षा
    ├── __init__.py
    └── test_sanskrit_coder.py
```

---

## 🔧 संस्थापनम् (Installation)

### 1. Python आवश्यकता

```bash
python --version  # Python 3.10+ आवश्यकम्
```

### 2. Project Download

```bash
cd /path/to/project
```

### 3. Dependencies Install

```bash
pip install -r requirements.txt
```

### 4. Test Run

```bash
python main.py
```

---

## 🚀 उपयोगः (Usage)

### आरम्भः (Starting)

```bash
python main.py
```

### स्वागतसन्देशः (Welcome Message)

```
🕉️ संस्कृत-कोडकः - स्वागतम्!

एतत् संस्कृत गणित-तर्क तन्त्रम् अस्ति।

आह्वानं कुर्वन्तु:
  गणय [expression]     - गणना कर्तुम्
  समाधत्स्व [equation] - समीकरणं समाधातुम्
  पश्य [formula]       - सूत्रं द्रष्टुम्
  अन्वेषय [topic]      - अन्वेषणं कर्तुम्
  भाषा [language]      - भाषां परिवर्तयितुम्
  सहायता              - सहायतां द्रष्टुम्

जयतु संस्कृतम्! 🙏
```

---

## 📖 आदेशाः (Commands)

### 1. गणय (Calculate)

**संस्कृत:**
```
>>> गणय ५ प्लस ३
परिणामः: 8 (अष्टौ)

>>> गणय १० गुणनम् ५
परिणामः: 50 (पञ्चाशत्)

>>> गणय १०० भागहार ४
परिणामः: 25.0 (पञ्चविंशति)
```

**English:**
```
>>> calculate 5 + 3
Result: 8

>>> calculate 10 * 5
Result: 50

>>> calculate 100 / 4
Result: 25.0
```

### 2. समाधत्स्व (Solve Equation)

**संस्कृत:**
```
>>> समाधत्स्व २x + ३ = ७
समाधानम्: x = 2

>>> समाधत्स्व ३x - ५ = १०
समाधानम्: x = 5
```

**English:**
```
>>> solve 2x + 3 = 7
Solution: x = 2

>>> solve 3x - 5 = 10
Solution: x = 5
```

### 3. पश्य (Show Formula)

**संस्कृत:**
```
>>> पश्य F = ma
सूत्रम् (Formula): F = ma
संस्कृतम् (Sanskrit): बलम् = द्रव्यमानम् × त्वरणम्
नाम (Name): Newton's Second Law
संस्कृत नाम (Sanskrit Name): न्यूटनस्य द्वितीय नियमः

चराः (Variables):
  F = Force (बलम्) - Newtons
  m = Mass (द्रव्यमानम्) - kg
  a = Acceleration (त्वरणम्) - m/s²
```

**English:**
```
>>> show F = ma
Formula: F = ma
Sanskrit: बलम् = द्रव्यमानम् × त्वरणम्
Name: Newton's Second Law
...
```

### 4. अन्वेषय (Search)

**संस्कृत:**
```
>>> अन्वेषय न्याय
विषयः (Topic): न्याय
नाम (Name): Nyaya
विवरणम् (Description): School of logic and epistemology
संस्कृतम् (Sanskrit): न्यायदर्शनम् षड्दर्शनेषु अन्यतमम्
```

**English:**
```
>>> search nyaya
Topic: Nyaya
Name: Nyaya
Description: School of logic and epistemology
...
```

### 5. भाषा (Language)

```
>>> भाषा sanskrit
भाषा परिवर्तितम्: sanskrit

>>> भाषा english
Language changed: english
```

---

## 📊 संख्याः (Numbers)

### देवनागरी अङ्काः (Devanagari Digits)

| Arabic | Sanskrit | Sanskrit Word |
|--------|----------|---------------|
| 0 | ० | शून्यम् |
| 1 | १ | एकम् |
| 2 | २ | द्वे |
| 3 | ३ | त्रीणि |
| 4 | ४ | चत्वारि |
| 5 | ५ | पञ्च |
| 6 | ६ | षट् |
| 7 | ७ | सप्त |
| 8 | ८ | अष्टौ |
| 9 | ९ | नव |
| 10 | १० | दश |

### गणित चिह्नानि (Math Symbols)

| English | Sanskrit | Symbol |
|---------|----------|--------|
| Plus | प्लस/योगः | + |
| Minus | ऋण/व्यवकलनम् | - |
| Multiply | गुणनम् | × |
| Divide | भागहार/विभाजनम् | ÷ |
| Equals | समानम् | = |
| Power | घात/शक्तिः | ^ |
| Root | मूलम् | √ |

---

## 🧪 परीक्षा (Testing)

### परीक्षा चालनम् (Run Tests)

```bash
python -m tests.test_sanskrit_coder
```

### परीक्षा फलम् (Test Results)

```
🕉️ संस्कृत-कोडकः - परीक्षा आरम्भः

==================================================

📊 संख्या परीक्षा (Number Tests)
------------------------------
✓ Sanskrit digits conversion
✓ Arabic digits conversion
✓ Number to Sanskrit word (5)
✓ Number to Sanskrit word (10)
✓ Sanskrit expression parsing

📚 अनुवादक परीक्षा (Translator Tests)
------------------------------
✓ Sanskrit text detection
✓ English text detection
✓ Sanskrit to English translation

🔢 गणित परीक्षा (Math Tests)
------------------------------
✓ Addition (2 + 3 = 5)
✓ Subtraction (10 - 4 = 6)
✓ Multiplication (3 * 4 = 12)
✓ Division (20 / 4 = 5)
✓ Formula lookup (F = ma)

📝 व्याकरण परीक्षा (Grammar Tests)
------------------------------
✓ Vibhakti lookup (Prathama)
✓ Lakara lookup (Lat)
✓ Command parsing

⚙️ इन्जिन् परीक्षा (Engine Tests)
------------------------------
✓ Engine calculation
✓ Welcome message
✓ Command processing

==================================================
परीक्षा समाप्तम्!
उत्तीर्णः (Passed): 19
अनुत्तीर्णः (Failed): 0
यशः (Success Rate): 100.0%
```

---

## 🎓 व्याकरणम् (Grammar)

### विभक्तयः (Cases)

संस्कृत-कोडकः सर्वाः अष्टौ विभक्तयः जानाति:

1. **प्रथमा** (Nominative) - कर्ता
2. **द्वितीया** (Accusative) - कर्म
3. **तृतीया** (Instrumental) - करणम्
4. **चतुर्थी** (Dative) - सम्प्रदानम्
5. **पञ्चमी** (Ablative) - अपादानम्
6. **षष्ठी** (Genitive) - सम्बन्धः
7. **सप्तमी** (Locative) - अधिकरणम्
8. **सम्बोधन** (Vocative) - आमन्त्रणम्

### लकाराः (Tenses)

1. **लट्** - Present (वर्तमानकालः)
2. **लङ्** - Past (भूतकालः)
3. **लृट्** - Future (भविष्यत्कालः)
4. **लोट्** - Imperative (आज्ञार्थः)
5. **लिङ्** - Optative (विध्यर्थः)
6. **लुङ्** - Aorist (अनद्यतनभूतकालः)
7. **लृङ्** - Conditional (सङ्केतार्थः)
8. **लिट्** - Perfect (परोक्षभूतकालः)

---

## 📚 सूत्राणि (Formulas)

### भौतिकशास्त्रम् (Physics)

| Formula | Sanskrit | Name |
|---------|----------|------|
| F = ma | बलम् = द्रव्यमानम् × त्वरणम् | Newton's 2nd Law |
| E = mc² | शक्तिः = द्रव्यमानम् × प्रकाशवेगः² | Mass-Energy |
| v = d/t | वेगः = दूरी / समयः | Velocity |
| KE = ½mv² | गतिजशक्तिः = ½ × द्रव्यमानम् × वेगः² | Kinetic Energy |

### ज्यामिति (Geometry)

| Formula | Sanskrit | Name |
|---------|----------|------|
| A = πr² | वृत्तस्य क्षेत्रफलम् = π × त्रिज्या² | Circle Area |
| C = 2πr | वृत्तस्य परिधिः = 2 × π × त्रिज्या | Circumference |

---

## 🛠️ विकासः (Development)

### नूतनं सूत्रं योजयतु (Add New Formula)

```python
# math_engine.py मध्ये
FORMULAS = {
    'your_formula': {
        'sanskrit': 'संस्कृत सूत्रम्',
        'name': 'Formula Name',
        'sanskrit_name': 'संस्कृत नाम',
        'variables': {
            'var': {'name': 'Variable', 'sanskrit': 'संस्कृत', 'unit': 'unit'},
        },
    },
}
```

### नूतनं गणितं योजयतु (Add New Math Function)

```python
# math_engine.py मध्ये
def your_function(self, params):
    """
    Your function description
    संस्कृत विवरणम्
    """
    # Implementation
    return result
```

---

## 🐛 त्रुटिनिवारणम् (Troubleshooting)

### सामान्यत्रुटयः (Common Errors)

**1. शून्येन विभाजनम् (Division by Zero)**
```
त्रुटि: शून्येन विभाजनम् असम्भवम्
Error: Division by zero is impossible
```

**2. अवैधं पदम् (Invalid Term)**
```
त्रुटि: अवैधं गणितं पदम्
Error: Invalid mathematical term
```

**3. संस्कृत अक्षराणि न सन्ति (No Sanskrit Characters)**
```
Check Unicode font support
```

---

## 📈 भविष्ययोजनाः (Future Plans)

### Version 2.0
- [ ] Calculus support (कलनम्)
- [ ] Statistics (सांख्यिकी)
- [ ] Matrix operations (मैट्रिक्स सञ्चालनम्)
- [ ] Graph plotting (आलेखं चित्रणम्)

### Version 3.0
- [ ] Voice input (वाक् इनपुट्)
- [ ] Handwriting recognition (हस्तलेखं पहचानम्)
- [ ] Mobile app (मोबाइल एप्लिकेशन)
- [ ] Web interface (वेब अन्तरफलक)

### Version 4.0
- [ ] AI-powered learning (कृत्रिमबुद्धि शिक्षणम्)
- [ ] Adaptive curriculum (अनुकूल पाठ्यक्रम)
- [ ] Multi-language support (बहुभाषा समर्थन)

---

## 🙏 कृतज्ञता (Acknowledgments)

### प्राचीनआचार्याः (Ancient Masters)

- **पाणिनिः** - Sanskrit Grammar (व्याकरणम्)
- **आर्यभटः** - Mathematics (गणितम्)
- **भास्कराचार्यः** - Algebra (बीजगणितम्)
- **ब्रह्मगुप्तः** - Zero & Numbers (शून्यं संख्याः)
- **नागार्जुनः** - Logic (तर्कशास्त्रम्)
- **कणादः** - Atomic Theory (अणुवादः)

### Modern Contributors

- Visionary RM (Raj Mitra) - Creator of Sanskrit Coder

---

## 📜 अनुज्ञापत्रम् (License)

**GNU AGPL v3**

स्वतन्त्रं सॉफ्टवेयरम्।  
कस्यचित् उपयोगाय मुक्तम्।  
Commercial use allowed.  
Modification allowed.  
Distribution allowed.

---

## 📞 सम्पर्कः (Contact)

**Project:** संस्कृत-कोडकः (Sanskrit Coder)  
**Version:** 1.0.0  
**Date:** March 8, 2026  
**Author:** Visionary RM (Raj Mitra)

---

## 🕉️ अन्तिमश्लोकः (Final Verse)

```
संस्कृतं देवभाषा च सर्वविज्ञानवाहिनी।
तकनीकेन संयुक्ता जगद्धितकरी भवेत्॥
```

*Sanskrit is the language of gods, carrier of all knowledge.*  
*Combined with technology, it becomes beneficial for the world.*

---

**जयतु संस्कृतम्! 🙏**  
*May Sanskrit Triumph!*

---

*Visionary RM (Raj Mitra)* ⚡  
*"संस्कृतम् अमरम् भवतु"* 🔥  
*"May Sanskrit Become Immortal"*
