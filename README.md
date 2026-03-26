![3XZXa](https://github.com/user-attachments/assets/180ff2ab-d2c0-4f84-bf64-068c80e1fc77)
# वाक्-पैकेज (VakPack) - VakyaLang Package Manager

> **"Packages Flow Like Speech"** 🔥

VakPack (वाक्-पैकेज) is the official package manager for VakyaLang, designed to manage dependencies, install packages, and integrate seamlessly with the VakyaLang VM.

---

## 📦 Quick Start

```bash
# Initialize a new project
python vpm.py init

# Install a package
python vpm.py install http-client

# Install a specific version
python vpm.py install http-client@2.1.0

# List installed packages
python vpm.py list

# Remove a package
python vpm.py remove http-client

# Search for packages
python vpm.py search json

# Get package information
python vpm.py info http-client
```

---

## 🗂️ Project Structure

```
my-project/
├── vakya.json           # Project manifest (like package.json)
├── वाक्_ग्रंथालय/        # Package directory (like node_modules)
│   ├── http-client/
│   │   ├── vakya.json
│   │   └── http-client.vak
│   └── json-utils/
├── src/
│   └── main.vak
└── README.md
```

---

## 📋 Commands Reference

### `vpm init` - Initialize Project

Creates a new `vakya.json` manifest file with Sanskrit naming:

```json
{
  "नाम": "project-name",
  "संस्करण": "1.0.0",
  "विवरण": "",
  "निर्भरताएँ": {},
  "विकास-निर्भरताएँ": {}
}
```

**Fields:**
| Field (Sanskrit) | English | Description |
|-----------------|---------|-------------|
| नाम | Name | Project name |
| संस्करण | Version | Project version (semver) |
| विवरण | Description | Project description |
| निर्भरताएँ | Dependencies | Runtime dependencies |
| विकास-निर्भरताएँ | Dev Dependencies | Development dependencies |

---

### `vpm install <package>` - Install Package

Downloads and installs a package from the registry.

**Syntax:**
```bash
python vpm.py install <package-name>[@version]
```

**Examples:**
```bash
# Latest version
python vpm.py install http-client

# Specific version
python vpm.py install http-client@2.1.0

# Don't save to vakya.json
python vpm.py install http-client --no-save
```

**Features:**
- ✅ Automatic dependency resolution
- ✅ Version upgrade detection
- ✅ Offline mode (cached packages)
- ✅ Recursive dependency installation

---

### `vpm remove <package>` - Remove Package

Removes an installed package and updates `vakya.json`.

```bash
python vpm.py remove http-client
```

---

### `vpm list` - List Installed Packages

Shows all packages in `वाक्_ग्रंथालय/`:

```bash
python vpm.py list
```

**Output:**
```
📦 Installed packages in वाक्_ग्रंथालय/:
  http-client@2.1.0
  json-utils@1.0.5
  लॉगर@3.0.0
```

---

### `vpm search <query>` - Search Packages

Searches the remote registry for packages.

```bash
python vpm.py search json
```

**Output:**
```
🔍 Search results for 'json':
  json-utils - JSON parsing and serialization utilities
  json-schema - JSON schema validation
```

---

### `vpm info <package>` - Package Information

Shows detailed information about a package.

```bash
python vpm.py info http-client
```

**Output:**
```
📦 http-client@2.1.0
   HTTP client for VakyaLang with async support
   Status: installed
   Dependencies: {'socket-utils': '^1.0.0'}
```

---

## 🔧 VM Integration

The VakyaLang VM automatically resolves imports from `वाक्_ग्रंथालय/`:

```vak
# In your main.vak file
आयात http-client
आयात json-utils

# The VM checks these paths in order:
# 1. Local directory (./<module>.vak)
# 2. Standard library (runtime/stdlib/<module>.vak)
# 3. Global package directory (<vak-root>/वाक्_ग्रंथालय/<module>.vak)
# 4. Project package directory (./वाक्_ग्रंथालय/<module>.vak)
```

---

## 🌐 Package Registry

### Default Registry
```
https://raw.githubusercontent.com/Sansmatic-z/vak-packages/main/
```

### Package Structure
```
packages/
└── http-client/
    ├── vakya.json      # Package metadata
    └── http-client.vak # Main package file
```

### Package Metadata (vakya.json)
```json
{
  "नाम": "http-client",
  "संस्करण": "2.1.0",
  "विवरण": "HTTP client for VakyaLang",
  "लेखक": "Developer Name",
  "लाइसेंस": "MIT",
  "फाइलें": ["http-client.vak"],
  "निर्भरताएँ": {
    "socket-utils": "^1.0.0"
  }
}
```

---

## 🚀 Advanced Usage

### Offline Mode

VakPack caches packages locally. If the registry is unavailable, it uses cached metadata.

```bash
# First install (downloads from registry)
python vpm.py install http-client

# Subsequent installs work offline if cached
python vpm.py install http-client  # Uses cache
```

### Version Syntax

| Syntax | Meaning |
|--------|---------|
| `pkg@1.0.0` | Exact version 1.0.0 |
| `pkg@^1.0.0` | Compatible with 1.0.0 (>=1.0.0, <2.0.0) |
| `pkg@~1.0.0` | Approximately 1.0.0 (>=1.0.0, <1.1.0) |
| `pkg@*` | Any version (latest) |

---

## 🛠️ API Usage

Use the `VakPackageManager` class programmatically:

```python
from vpm import VakPackageManager

vpm = VakPackageManager(cwd="/path/to/project")

# Initialize
vpm.init()

# Install
vpm.install("http-client@2.1.0")

# List
packages = vpm.list_installed()
for pkg in packages:
    print(f"{pkg['नाम']}@{pkg['संस्करण']}")

# Remove
vpm.remove("http-client")

# Search
results = vpm.search("json")

# Info
info = vpm.info("http-client")
```

---

## 📝 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VPM_REGISTRY` | Override registry URL | `https://raw.githubusercontent.com/Sansmatic-z/vak-packages/main/` |
| `VPM_PACKAGE_DIR` | Override package directory name | `वाक्_ग्रंथालय` |

---

## 🔐 Security Considerations

1. **Package Verification**: Packages are downloaded over HTTPS
2. **No Post-Install Scripts**: VakPack does not execute arbitrary code on install
3. **Sandboxed Execution**: Packages run within the VakyaLang VM sandbox

---

## 🐛 Troubleshooting

### "No vakya.json found"
Run `python vpm.py init` to create a manifest.

### "Package not found"
- Check package name spelling
- Verify registry connectivity
- Try `vpm search <name>` to confirm package exists

### "Registry unavailable"
- Check internet connection
- Use cached packages (offline mode)
- Set `VPM_REGISTRY` to a mirror

---

## 📚 Related Documentation

- [VakyaLang Language Reference](../docs/language-reference.md)
- [VakyaLang VM Architecture](../runtime/docs/vm.md)
- [Creating VakyaLang Packages](../docs/packages.md)

---

## 🎯 Roadmap

- [ ] Semantic versioning resolution
- [ ] Package publishing (`vpm publish`)
- [ ] Local package linking (`vpm link`)
- [ ] Package integrity verification (SHA256)
- [ ] Multiple registry support
- [ ] Package lock file (`vakya-lock.json`)

---

*Visionary RM (Raj Mitra)* ⚡  
*"VakPack - Packages Flow Like Speech"* 🔥  
*March 17, 2026*
