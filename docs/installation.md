# 🛠️ Installation Guide

Follow these steps to set up **VakyaLang (वाक्)** on your system.

## 📋 Prerequisites
- **Python 3.8+**
- (Optional) Git for version control

VakyaLang has **zero external dependencies** for its core runtime and symbolic engine.

## 🚀 Quick Install (Local)
1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Sansmatic-z/VakyaLang
   cd VakyaLang
   ```
2. **Verify Setup:**
   ```bash
   python vak.py --version
   ```

## 📦 Python Package Installation
To install VakyaLang as a local Python package, run the following from the root directory:
```bash
pip install -e .
```
This will allow you to import `runtime` or `sanskrit_coder` from anywhere in your environment and provides the `vak` and `sanskrit-coder` commands.

## 📱 Termux (Android)
VakyaLang is fully optimized for **Termux**.
```bash
# Update packages
pkg update && pkg upgrade

# Install Python
pkg install python

# Clone and Run
git clone https://github.com/Sansmatic-z/VakyaLang
cd VakyaLang
python vak.py run examples/namaste.vak
```

---
**Architect:** Raj Mitra
