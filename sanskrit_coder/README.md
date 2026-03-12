# 🕉️ संस्कृत-कोडकः (Sanskrit Coder)

[![AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Part of VakyaLang](https://img.shields.io/badge/Part%20of-VakyaLang-8B00FF.svg)](https://github.com/Sansmatic-z/VakyaLang)

**पूर्णं संस्कृत निष्पादन तन्त्रम्**  
*Complete Sanskrit Execution System*

A symbolic mathematics, logic and grammar engine that speaks Sanskrit natively — powered by Nyāya reasoning and Pāṇinian grammar.

---

## 🚀 Quick Start (Recommended)

```bash
# From the main VakyaLang repository
pip install -e .
sanskrit-coder
```

(Uses the official `sanskrit-coder` CLI from `pyproject.toml` — no manual `requirements.txt` needed.)

---

## विशेषताः (Features)
- Full Sanskrit input/output (Devanagari + spoken commands)
- Sanskrit Numbers, Grammar (Vibhakti, Lakara), Mathematics & Nyāya Logic
- Auto Sanskrit ↔ English translation
- Formula lookup, equation solving, physics/grammar engine

---

## ⚖️ Licensing & Legal Protection (Very Important)

**This is original research by Raj Mitra (2026).**

- Licensed under **GNU AGPL v3.0** (same as the rest of VakyaLang runtime)
- Part of the main VakyaLang project
- **You MUST** include the root `NOTICE` file and all copyright headers in any copy or derivative work.

See the root files for full legal text:  
`../LICENSE_AGPL`, `../NOTICE`, `../LICENSE`

**© 2026 Raj Mitra. All Rights Reserved.**  
Any use, modification, or redistribution without proper credit and AGPL compliance is prohibited.

---

## 🎯 उद्देश्यम् (Purpose)

संस्कृतभाषायां पूर्णं गणित-तर्क-निष्पादनतन्त्रम्।  
A complete mathematics and logic execution system in Sanskrit language.

---

## ✨ विशेषताः (Features)

| संस्कृत | English |
|---------|---------|
| संस्कृत संख्याः (०-९) | Sanskrit Numbers (0-9) |
| संस्कृत व्याकरणम् | Sanskrit Grammar Engine |
| संस्कृत गणितम् | Sanskrit Mathematics |
| संस्कृत तर्कशास्त्रम् | Sanskrit Logic System |
| संस्कृत आदेशाः | Sanskrit Commands |
| संस्कृत परिणामाः | Sanskrit Results |
| संस्कृत त्रुटयः | Sanskrit Error Messages |

---

## 📦 संस्थापनम् (Installation)

```bash
# Recommendation: Use 'pip install -e .' from the root directory.
# Alternative manual install:
cd sanskrit_coder
pip install -r requirements.txt
```

---

## 🚀 उपयोगः (Usage)

### मूलगणितम् (Basic Arithmetic)

```python
from sanskrit_coder import SanskritEngine

engine = SanskritEngine()

# संस्कृत input
result = engine.gणय("५ प्लस ३")
print(result)  # ८ (अष्टौ)

# English input (auto-translated)
result = engine.calculate("5 plus 3")
print(result)  # 8
```

### बीजगणितम् (Algebra)

```python
# समीकरणं समाधत्स्व (Solve equation)
result = engine.sमाधत्स्व("२x + ३ = ७")
print(result)  # x = २
```

### सूत्राणि (Formulas)

```python
# भौतिकशास्त्र सूत्रम् (Physics formula)
result = engine.pश्य("F = ma")
print(result)
# बलम् = द्रव्यमानम् × त्वरणम्
```

---

## 📂 सञ्चिकाः (File Structure)

```
sanskrit_coder/
├── README.md              # इयं सञ्चिका (This file)
├── LICENSE                # Module License
├── requirements.txt       # आवश्यकताः (Dependencies)
│
├── core/                  # मुख्य भागः (Core)
│   ├── __init__.py
│   ├── engine.py          # मुख्य इन्जिन् (Main Engine)
│   ├── translator.py      # संस्कृत↔English अनुवादः
│   └── unicode.py         # संस्कृत Unicode handling
│
├── numbers/               # संख्या पद्धतिः
│   ├── __init__.py
│   ├── sanskrit_numbers.py  # ०-९ handling
│   └── number_words.py    # एकम्, द्वे, त्रीणि...
│
├── grammar/               # व्याकरणम्
│   ├── __init__.py
│   ├── vibhakti.py        # विभक्तयः (Cases)
│   ├── lakara.py          # लकाराः (Tenses)
│   └── sentence.py        # वाक्यर रचना (Syntax)
│
├── math/                  # गणितम्
│   ├── __init__.py
│   ├── arithmetic.py      # अङ्कगणितम्
│   ├── algebra.py         # बीजगणितम्
│   └── geometry.py        # रेखागणितम्
│
├── logic/                 # तर्कशास्त्रम्
│   ├── __init__.py
│   ├── nyaya.py           # न्याय तर्कः
│   └── inference.py       # अनुमानम्
```

---

## 📖 संस्कृत शब्दावली (Sanskrit Vocabulary)

### गणित सञ्चालनम् (Math Operations)

| संस्कृत | English | Symbol |
|---------|---------|--------|
| प्लस / योगः | Plus | + |
| ऋण / व्यवकलनम् | Minus | - |
| गुणनम् | Multiply | × |
| भागहार / विभाजनम् | Divide | ÷ |
| घात / शक्तिः | Power | ^ |
| मूलम् | Root | √ |

### संख्याः (Numbers)

| Devanagari | Sanskrit | English |
|------------|----------|---------|
| ० | शून्यम् | 0 |
| १ | एकम् | 1 |
| २ | द्वे | 2 |
| ३ | त्रीणि | 3 |
| ४ | चत्वारि | 4 |
| ५ | पञ्च | 5 |
| ६ | षट् | 6 |
| ७ | सप्त | 7 |
| ८ | अष्टौ | 8 |
| ९ | नव | 9 |
| १० | दश | 10 |

### आदेशाः (Commands)

| संस्कृत | English | Usage |
|---------|---------|-------|
| गणय | Calculate | गणय ५ प्लस ३ |
| समाधत्स्व | Solve | समाधत्स्व २x + ३ = ७ |
| दर्शय | Show | दर्शय सूत्रम् F=ma |
| अन्वेषय | Search | अन्वेषय बलम् |
| परिवर्तय | Convert | परिवर्तय १०० मीटर to किलोमीटर |

---

## 🧪 उदाहरणानि (Examples)

### Example 1: Simple Addition

```python
>>> from sanskrit_coder import SanskritEngine
>>> engine = SanskritEngine()
>>> engine.gणय("७ प्लस ५")
'१२ (द्वादश)'
```

### Example 2: Complex Expression

```python
>>> engine.gणय("(१० ऋण ३) गुणनम् २")
'१४ (चतुर्दश)'
```

### Example 3: Equation Solving

```python
>>> engine.sमाधत्स्व("३x + ५ = १४")
'x = ३'
```

### Example 4: Formula Lookup

```python
>>> engine.pश्य("E = mc²")
'शक्तिः = द्रव्यमानम् × प्रकाशवेगः²'
```

---

## 🎓 व्याकरण तन्त्रम् (Grammar System)

### विभक्तयः (Cases)

The system understands all 8 Sanskrit cases:

1. **प्रथमा** (Nominative) - कर्ता
2. **द्वितीया** (Accusative) - कर्म
3. **तृतीया** (Instrumental) - करणम्
4. **चतुर्थी** (Dative) - सम्प्रदानम्
5. **पञ्चमी** (Ablative) - अपादानम्
6. **षष्ठी** (Genitive) - सम्बन्धः
7. **सप्तमी** (Locative) - अधिकरणम्
8. **सम्बोधन** (Vocative) - आमन्त्रणम्

### लकाराः (Tenses)

| लकार | English | Example |
|------|---------|---------|
| लट् | Present | गणयति (calculates) |
| लङ् | Past | गणयत् (calculated) |
| लृट् | Future | गणयिष्यति (will calculate) |
| लोट् | Imperative | गणयतु (let him calculate) |

---

## 🔧 तकनीकी विवरणम् (Technical Details)

### Requirements

- Python 3.10+
- Sanskrit Unicode support
- No external NLP libraries required (built-in)

---

## 🙏 कृतज्ञता (Acknowledgments)

- पाणिनिः (Panini) - Sanskrit Grammar
- आर्यभटः (Aryabhata) - Mathematics
- भास्कराचार्यः (Bhaskaracharya) - Algebra
- नागार्जुनः (Nagarjuna) - Logic

---

## 📞 सम्पर्कः (Contact)

**संस्कृत-कोडकः**  
*Reviving Sanskrit Through Technology*

---

*"संस्कृतम् अमरम् भवतु"*  
**Visionary RM (Raj Mitra)** ⚡  
[Back to main VakyaLang](https://github.com/Sansmatic-z/VakyaLang)

**Version:** 2.0.0  
**Date:** March 12, 2026  
**Status:** Active Development
