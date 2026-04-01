#!/usr/bin/env python3
# वाक् भाषा - पुस्तकालय पैकेजर
# Vak Language - Library Packager
# Creates compressed .tar.gz bundles of VakyaLang libraries

"""
VakyaLang Library Packager
═══════════════════════════════════════════════════════════════
Creates compressed package bundles for distribution via VPM.

Usage:
    python package_lib.py                          # Package all stdlib
    python package_lib.py --lib rekha_ganit        # Package specific library
    python package_lib.py --output ./packages      # Custom output directory
"""

import os
import sys
import tarfile
import gzip
import shutil
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime


class VakPackageBuilder:
    """Builds compressed VakyaLang library packages"""
    
    def __init__(self, stdlib_dir: str = None, output_dir: str = None):
        self.stdlib_dir = stdlib_dir or Path(__file__).parent
        self.output_dir = output_dir or Path(__file__).parent / "packages"
        self.output_dir.mkdir(exist_ok=True)
    
    def get_libraries(self) -> list:
        """Get list of available libraries"""
        libs = []
        for f in self.stdlib_dir.glob("*.vak"):
            if not f.name.startswith('_'):
                libs.append(f.stem)
        return sorted(libs)
    
    def calculate_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def count_lines(self, filepath: str) -> int:
        """Count non-empty lines in file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    
    def package_single(self, lib_name: str, version: str = "1.0.0") -> str:
        """
        Package a single library into .tar.gz
        
        Args:
            lib_name: Name of library (without .vak extension)
            version: Version string
        
        Returns:
            Path to created package
        """
        lib_file = self.stdlib_dir / f"{lib_name}.vak"
        if not lib_file.exists():
            raise FileNotFoundError(f"Library not found: {lib_name}")
        
        # Create package metadata
        metadata = {
            "नाम": lib_name,
            "संस्करण": version,
            "विवरण": f"VakyaLang {lib_name} library",
            "लेखक": "Raj Mitra",
            "लाइसेंस": "AGPL-3.0",
            "निर्मित": datetime.now().isoformat(),
            "फाइलें": [f"{lib_name}.vak"],
            "पंक्तियाँ": self.count_lines(str(lib_file)),
            "हैश": self.calculate_hash(str(lib_file))
        }
        
        # Create temporary directory for package
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / lib_name
            pkg_dir.mkdir()
            
            # Copy library file
            shutil.copy(lib_file, pkg_dir / f"{lib_name}.vak")
            
            # Write metadata
            with open(pkg_dir / "vakya.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Create README
            readme_content = f"""# {lib_name} - VakyaLang Library

Version: {version}
Author: Raj Mitra
License: AGPL-3.0

## Usage

```vak
आयात {lib_name}
```

## Description

Part of the VakyaLang Standard Library.
"""
            with open(pkg_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create compressed package
            output_path = self.output_dir / f"{lib_name}-{version}.tar.gz"
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(pkg_dir, arcname=lib_name)
        
        print(f"✅ Package created: {output_path}")
        print(f"   Hash: {metadata['हैश'][:16]}...")
        print(f"   Lines: {metadata['पंक्तियाँ']}")
        
        return str(output_path)
    
    def package_all(self, version: str = "1.0.0") -> list:
        """Package all libraries"""
        libs = self.get_libraries()
        packages = []
        
        print(f"📦 Packaging {len(libs)} libraries...")
        print("=" * 50)
        
        for lib in libs:
            try:
                pkg_path = self.package_single(lib, version)
                packages.append(pkg_path)
            except Exception as e:
                print(f"❌ Failed to package {lib}: {e}")
        
        print("=" * 50)
        print(f"✅ Successfully packaged {len(packages)}/{len(libs)} libraries")
        
        return packages
    
    def create_stdlib_bundle(self, version: str = "1.0.0") -> str:
        """Create complete stdlib bundle"""
        libs = self.get_libraries()
        
        # Create metadata for bundle
        metadata = {
            "नाम": "vakya-stdlib-bundle",
            "संस्करण": version,
            "विवरण": "Complete VakyaLang Standard Library Bundle",
            "लेखक": "Raj Mitra",
            "लाइसेंस": "AGPL-3.0",
            "निर्मित": datetime.now().isoformat(),
            "पुस्तकालय": libs,
            "कुल_पुस्तकालय": len(libs)
        }
        
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg_dir = Path(tmpdir) / "vakya-stdlib-bundle"
            pkg_dir.mkdir()
            
            # Copy all library files
            for lib in libs:
                lib_file = self.stdlib_dir / f"{lib}.vak"
                if lib_file.exists():
                    shutil.copy(lib_file, pkg_dir / f"{lib}.vak")
            
            # Copy Python bridge
            bridge_file = self.stdlib_dir / "py_bridge.py"
            if bridge_file.exists():
                shutil.copy(bridge_file, pkg_dir / "py_bridge.py")
            
            # Write metadata
            with open(pkg_dir / "vakya.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Create comprehensive README
            readme_content = f"""# VakyaLang Standard Library Bundle

**Version:** {version}  
**Author:** Raj Mitra  
**License:** AGPL-3.0  
**Created:** {metadata['निर्मित']}

## Included Libraries ({len(libs)} total)

"""
            for lib in libs:
                readme_content += f"- `{lib}`\n"
            
            readme_content += f"""

## Installation

### Using VPM (recommended)
```bash
python vpm.py install vakya-stdlib-bundle@{version}
```

### Manual Installation
1. Extract the archive
2. Copy `.vak` files to your `वाक्_ग्रंथालय/` directory

## Usage

```vak
# Import any library
आयात rekha_ganit      # Linear algebra
आयात data_sangrah     # Data structures
आयात kootlekh         # Cryptography
आयात yadricha         # Random utilities
आयात py_bridge        # Python interop
```

## Python Bridge

The bundle includes `py_bridge.py` for Python interoperability:

```vak
आयात py_bridge

# Use Python libraries
चर math = py_bridge.पायथन_आयात("math")
चर result = math.sqrt(16)
```

## Requirements

- VakyaLang Runtime v2.17.0+
- Python 3.8+ (for py_bridge)

## License

AGPL-3.0 - Free to use, modify, and distribute.

---
*Visionary RM (Raj Mitra)* ⚡
"""
            
            with open(pkg_dir / "README.md", 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            # Create compressed bundle
            output_path = self.output_dir / f"vakya-stdlib-bundle-{version}.tar.gz"
            with tarfile.open(output_path, "w:gz") as tar:
                tar.add(pkg_dir, arcname="vakya-stdlib-bundle")
        
        print(f"✅ Stdlib bundle created: {output_path}")
        return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description='VakyaLang Library Packager',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--lib', '-l', help='Package specific library')
    parser.add_argument('--version', '-v', default='1.0.0', help='Version string')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--bundle', '-b', action='store_true', help='Create stdlib bundle')
    parser.add_argument('--list', action='store_true', help='List available libraries')
    
    args = parser.parse_args()
    
    builder = VakPackageBuilder(output_dir=args.output)
    
    if args.list:
        libs = builder.get_libraries()
        print(f"📚 Available libraries ({len(libs)}):")
        for lib in libs:
            print(f"   - {lib}")
        return
    
    if args.lib:
        builder.package_single(args.lib, args.version)
    elif args.bundle:
        builder.create_stdlib_bundle(args.version)
    else:
        builder.package_all(args.version)


if __name__ == "__main__":
    main()
