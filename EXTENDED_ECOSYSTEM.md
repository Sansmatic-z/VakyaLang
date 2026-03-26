# 🚀 VakyaLang Extended Ecosystem

## Overview

VakyaLang has been expanded with a comprehensive ecosystem of libraries, Python interop, and package management capabilities.

---

## 📚 New Standard Library Modules

### 1. **रेखा गणित (rekha_ganit)** - Linear Algebra

Advanced vector and matrix operations:

```vak
आयात rekha_ganit

# Vector operations
चर v1 = [३, ४, ०]
चर v2 = [१, २, ०]

चर योग = rekha_ganit.सदिश_योग(v1, v2)
चर डॉट = rekha_ganit.सदिश_गुणनफल(v1, v2)
चर लंबाई = rekha_ganit.सदिश_लंबाई(v1)

# Matrix operations
चर m1 = [[१, २], [३, ४]]
चर m2 = [[५, ६], [७, ८]]

चर product = rekha_ganit.मैट्रिक्स_गुणन(m1, m2)
चर det = rekha_ganit.मैट्रिक्स_निर्धारक(m1)
```

**Features:**
- Vector addition, subtraction, scalar multiplication
- Dot product, cross product (3D)
- Vector magnitude and normalization
- Matrix operations (add, subtract, multiply)
- Matrix transpose and determinant
- Matrix inverse (2x2 supported)

---

### 2. **डाटा संग्रह (data_sangrah)** - Data Structures

Complete collection of data structures:

```vak
आयात data_sangrah

# Stack (LIFO)
चर stack = नव स्टैक()
stack.धक्का(10)
stack.पॉप()

# Queue (FIFO)
चर queue = नव कतार()
queue.प्रवेश(1)
queue.निर्गम()

# Linked List
चर list = नव लिंक्ड_लिस्ट()
list.जोड़ो(100)
list.हटाओ(100)

# Binary Search Tree
चर tree = नव बाइनरी_सर्च_ट्री()
tree.जोड़ो(50)
tree.खोजो(50)

# Hash Table
चर hash = नव हैश_टेबल(10)
hash.डालो("key", "value")
hash.प्राप्त_करो("key")
```

**Data Structures:**
- `स्टैक` - Stack (LIFO)
- `कतार` - Queue (FIFO)
- `लिंक्ड_लिस्ट` - Singly Linked List
- `बाइनरी_सर्च_ट्री` - Binary Search Tree
- `हैश_टेबल` - Hash Table / Dictionary

---

### 3. **कूटलेखन (kootlekh)** - Cryptography

Hash functions and encryption utilities:

```vak
आयात kootlekh

# Hash functions
चर hash = kootlekh.SHA256("message")
चर md5 = kootlekh.MD5("message")

# HMAC authentication
चर signature = kootlekh.HMAC_निरूपण(data, key)
चर valid = kootlekh.HMAC_सत्यापन(data, key, signature)

# Password hashing
चर [hash, salt] = kootlekh.पासवर्ड_हैश(password)
चर valid = kootlekh.पासवर्ड_जाँच(password, salt, hash)

# Base64 encoding
चर encoded = kootlekh.बेस64_एन्कोड("text")
चर decoded = kootlekh.बेस64_डिकोड(encoded)

# Secure tokens
चर token = kootlekh.सुरक्षित_टोकन_बनाओ(32)
```

**Features:**
- SHA-256, SHA-512, MD5, SHA-1 hashing
- HMAC message authentication
- Password hashing with salt
- Base64 encoding/decoding
- Secure token generation

---

### 4. **यादृच्छा (yadricha)** - Random Utilities

Random number generation (via Python bridge):

```vak
आयात yadricha

चर rand_int = yadricha.यादृच्छा_पूर्णांक(1, 100)
चर rand_float = yadricha.यादृच्छा_दशमलव()
चर choice = yadricha.यादृच्छा_चयन([1, 2, 3])
```

---

### 5. **पायथन ब्रिज (py_bridge)** - Python Interoperability

Call any Python library from VakyaLang:

```vak
आयात py_bridge

# Import Python modules
चर math = py_bridge.पायथन_आयात("math")
चर result = math.sqrt(16)

# Import multiple modules
चर requests = py_bridge.पायथन_आयात("requests")
चर response = requests.get("https://api.example.com")

# Use Python libraries
चर np = py_bridge.पायथन_आयात("numpy")
चर array = np.array([1, 2, 3])
```

**Supported Python Libraries:**
- `math` - Mathematical functions
- `random` - Random number generation
- `json` - JSON parsing/generation
- `os` - Operating system interface
- `datetime` - Date/time handling
- `collections` - Data structures
- `requests` - HTTP requests
- `numpy` - Numerical computing
- `pandas` - Data analysis
- Any other Python library!

---

## 🐍 Python Dependencies

VakyaLang now supports installing Python packages:

### Install Python Packages

```bash
# Install single package
python vpm.py install-py requests

# Install with version
python vpm.py install-py numpy --version ">=1.24.0"

# Install multiple packages
python vpm.py install-py requests numpy pandas
```

### Optional Dependency Groups (pyproject.toml)

```bash
# Install web scraping tools
pip install vakyalang[web]

# Install data science stack
pip install vakyalang[data]

# Install plotting libraries
pip install vakyalang[plotting]

# Install machine learning
pip install vakyalang[ml]

# Install everything
pip install vakyalang[all]
```

---

## 📦 Package Bundles

### Create Library Bundles

```bash
# Create stdlib bundle
python vpm.py bundle --version 1.0.0

# Bundle specific library
python vpm.py bundle --lib rekha_ganit --version 1.0.0

# Bundle all libraries
python vpm.py bundle --all --output ./packages
```

### Install from Bundle

```bash
# Install from local .tar.gz file
python vpm.py install ./packages/vakya-stdlib-bundle-1.0.0.tar.gz
```

---

## 📋 Updated VPM Commands

| Command | Description |
|---------|-------------|
| `vpm init` | Initialize new project |
| `vpm install <pkg>` | Install package (registry or local file) |
| `vpm install-py <pkg>` | Install Python dependency |
| `vpm remove <pkg>` | Remove package |
| `vpm list` | List installed packages |
| `vpm list --python` | List Python dependencies |
| `vpm search <query>` | Search packages |
| `vpm info <pkg>` | Package information |
| `vpm bundle` | Create library bundles |

---

## 🗂️ Project Structure

```
vakyalang-upgraded/
├── runtime/
│   ├── stdlib/              # Standard library
│   │   ├── mool.vak         # Core utilities
│   │   ├── rekha_ganit.vak  # ← NEW: Linear algebra
│   │   ├── data_sangrah.vak # ← NEW: Data structures
│   │   ├── kootlekh.vak     # ← NEW: Cryptography
│   │   ├── yadricha.vak     # ← NEW: Random utilities
│   │   └── py_bridge.py     # ← NEW: Python interop
│   └── ...
├── examples/
│   ├── rekha_ganit_udaharan.vak    # ← NEW
│   ├── data_sangrah_udaharan.vak   # ← NEW
│   ├── kootlekh_udaharan.vak       # ← NEW
│   └── py_bridge_udaharan.vak      # ← NEW
├── packages/                        # ← NEW: Bundle directory
│   └── vakya-stdlib-bundle-1.0.0.tar.gz
├── pyproject.toml                   # ← UPDATED: Optional deps
├── vpm.py                          # ← UPDATED: New commands
└── package_lib.py                  # ← NEW: Packager
```

---

## 🎯 Usage Examples

### Linear Algebra with Python NumPy

```vak
आयात py_bridge

# Use NumPy for advanced linear algebra
चर np = py_bridge.पायथन_आयात("numpy")

चर arr1 = np.array([[1, 2], [3, 4]])
चर arr2 = np.array([[5, 6], [7, 8]])

चर result = np.matmul(arr1, arr2)
मुद्रय "Matrix multiplication:", result

चर eigenvalues = np.linalg.eig(arr1)
मुद्रय "Eigenvalues:", eigenvalues
```

### Web Scraping with Requests + BeautifulSoup

```vak
आयात py_bridge

चर requests = py_bridge.पायथन_आयात("requests")
चर bs4 = py_bridge.पायथन_आयात("bs4")

चर response = requests.get("https://example.com")
चर soup = bs4.BeautifulSoup(response.text, "html.parser")

चर title = soup.title.string
मुद्रय "Page title:", title
```

### Data Analysis with Pandas

```vak
आयात py_bridge

चर pd = py_bridge.पायथन_आयात("pandas")

# Create DataFrame
चर data = {"name": ["राज", "श्याम"], "age": [25, 30]}
चर df = pd.DataFrame(data)

मुद्रय "DataFrame:", df
मुद्रय "Mean age:", df.age.mean()
```

---

## 📊 Capability Comparison

| Feature | Before | After |
|---------|--------|-------|
| Standard Libraries | 11 basic | 16+ (5 new advanced) |
| Python Interop | Limited | Full bridge to ALL Python libs |
| Package Formats | Registry only | Registry + .tar.gz bundles |
| Dependencies | VakyaLang only | VakyaLang + Python packages |
| Data Structures | Basic lists/dicts | Stack, Queue, BST, Hash Table |
| Math | Basic arithmetic | Linear algebra, vectors, matrices |
| Cryptography | None | SHA, HMAC, password hashing |
| Random | None | Full random number generation |

---

## 🔧 Installation

### Install Extended Libraries

```bash
# Install VakyaLang with all dependencies
pip install vakyalang[all]

# Or install specific groups
pip install vakyalang[data]    # Data science
pip install vakyalang[web]     # Web scraping
pip install vakyalang[ml]      # Machine learning
```

### Use Local Libraries

```vak
# Import from stdlib
आयात rekha_ganit
आयात data_sangrah
आयात kootlekh
आयात py_bridge
```

---

## 📚 Example Programs

Run the example programs to see capabilities:

```bash
# Linear algebra examples
python vak.py examples/rekha_ganit_udaharan.vak

# Data structures examples
python vak.py examples/data_sangrah_udaharan.vak

# Cryptography examples
python vak.py examples/kootlekh_udaharan.vak

# Python bridge examples
python vak.py examples/py_bridge_udaharan.vak
```

---

## 🎓 Learning Resources

- **Linear Algebra**: See `examples/rekha_ganit_udaharan.vak`
- **Data Structures**: See `examples/data_sangrah_udaharan.vak`
- **Cryptography**: See `examples/kootlekh_udaharan.vak`
- **Python Bridge**: See `examples/py_bridge_udaharan.vak`

---

## 🚀 Future Enhancements

Planned additions:
- [ ] More standard library modules (networking, async I/O)
- [ ] Direct NumPy/Pandas integration in VakyaLang syntax
- [ ] Plotting/visualization library
- [ ] Database connectors (SQLite, PostgreSQL)
- [ ] Web framework (HTTP server, routing)
- [ ] Machine learning wrappers

---

*Visionary RM (Raj Mitra)* ⚡  
*"VakyaLang - Now with Extended Capabilities"* 🔥  
*March 19, 2026*
