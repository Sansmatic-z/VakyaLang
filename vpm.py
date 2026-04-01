#!/usr/bin/env python3
# वाक् भाषा - पैकेज प्रबंधक (VakPack Package Manager)
# Vak Language - Package Manager CLI
#
# ═══════════════════════════════════════════════════════════════════════════
# Signature: Visionary RM (Raj Mitra) ⚡
# Created: March 17, 2026
# "VakPack - Packages Flow Like Speech" 🔥
# ═══════════════════════════════════════════════════════════════════════════

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import shutil
import tarfile
import gzip
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any

# Default registry URL (can be overridden)
DEFAULT_REGISTRY = "https://raw.githubusercontent.com/Sansmatic-z/vak-packages/main/"

# Package directory name (like node_modules)
PACKAGE_DIR = "वाक्_ग्रंथालय"

# Python dependencies marker
PYTHON_DEPS_MARKER = ".python_deps.json"


def _safe_print(*args, **kwargs):
    file = kwargs.pop("file", sys.stdout)
    sep = kwargs.pop("sep", " ")
    end = kwargs.pop("end", "\n")
    flush = kwargs.pop("flush", False)
    if kwargs:
        raise TypeError(f"Unsupported print kwargs: {', '.join(kwargs)}")

    text = sep.join(str(arg) for arg in args) + end
    try:
        file.write(text)
    except UnicodeEncodeError:
        encoding = getattr(file, "encoding", None) or "utf-8"
        safe_text = text.encode(encoding, errors="backslashreplace").decode(
            encoding,
            errors="replace",
        )
        file.write(safe_text)
    if flush and hasattr(file, "flush"):
        file.flush()


print = _safe_print


class VakPackageManager:
    """
    VakyaLang Package Manager (VakPack).
    
    Manages installation, removal, and dependency resolution for VakyaLang packages.
    
    Commands:
    - vpm init: Initialize a new project with vakya.json
    - vpm install <package>: Install a package
    - vpm remove <package>: Remove a package
    - vpm list: List installed packages
    - vpm search <query>: Search for packages
    - vpm info <package>: Show package information
    """
    
    def __init__(self, cwd: str = None):
        """Initialize package manager."""
        self.cwd = cwd or os.getcwd()
        self.package_dir = os.path.join(self.cwd, PACKAGE_DIR)
        self.manifest_path = os.path.join(self.cwd, "vakya.json")
        self.registry_url = os.getenv("VPM_REGISTRY", DEFAULT_REGISTRY)
        if not self.registry_url.endswith("/"):
            self.registry_url += "/"

    def _ensure_package_dir(self) -> None:
        os.makedirs(self.package_dir, exist_ok=True)

    def _safe_relative_path(self, path: str) -> str:
        normalized = os.path.normpath(path).replace("\\", "/")
        if not normalized or normalized in {".", ".."}:
            raise ValueError("Empty package path is not allowed")
        if normalized.startswith("../") or normalized.startswith("/") or os.path.isabs(path):
            raise ValueError(f"Unsafe package path: {path}")
        return normalized

    def _safe_join(self, root: str, relative_path: str) -> str:
        normalized = self._safe_relative_path(relative_path)
        root_abs = os.path.abspath(root)
        candidate = os.path.abspath(os.path.join(root_abs, normalized))
        if os.path.commonpath([root_abs, candidate]) != root_abs:
            raise ValueError(f"Unsafe package path: {relative_path}")
        return candidate

    def _sync_module_entrypoint(self, package_name: str, metadata: Dict[str, Any], package_path: str) -> None:
        init_path = os.path.join(package_path, "__init__.vak")
        if os.path.exists(init_path):
            return

        files = metadata.get("फाइलें", [])
        entry_relative = None
        preferred_names = (
            f"{package_name}.vak",
            "main.vak",
        )
        for preferred in preferred_names:
            for file_path in files:
                normalized = self._safe_relative_path(file_path)
                if os.path.basename(normalized) == preferred:
                    entry_relative = normalized
                    break
            if entry_relative is not None:
                break
        if entry_relative is None:
            for file_path in files:
                normalized = self._safe_relative_path(file_path)
                if normalized.endswith(".vak") and "/" not in normalized:
                    entry_relative = normalized
                    break
        if entry_relative is None:
            return

        source_path = self._safe_join(package_path, entry_relative)
        if not os.path.exists(source_path):
            return

        alias_path = os.path.join(self.package_dir, f"{package_name}.vak")
        shutil.copyfile(source_path, alias_path)
    
    def init(self) -> bool:
        """
        Initialize a new project with vakya.json manifest.
        
        Creates a basic vakya.json file with:
        {
            "नाम": "project-name",
            "संस्करण": "1.0.0",
            "विवरण": "",
            "निर्भरताएँ": {}
        }
        """
        if os.path.exists(self.manifest_path):
            print(f"⚠️  vakya.json already exists")
            return False
        
        project_name = os.path.basename(self.cwd) or "अज्ञात-परियोजना"
        
        manifest = {
            "नाम": project_name,
            "संस्करण": "1.0.0",
            "विवरण": "",
            "निर्भरताएँ": {},
            "विकास-निर्भरताएँ": {}
        }
        
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        # Create package directory
        self._ensure_package_dir()
        
        print(f"✅ Initialized vakya.json in {self.cwd}")
        print(f"📦 Package directory: {PACKAGE_DIR}/")
        return True
    
    def install(self, package_name: str, version: str = None, save: bool = True) -> bool:
        """
        Install a package from the registry or local file.

        Downloads package files and places them in वाक्_ग्रंथालय/<package-name>/
        
        Supports:
        - Registry packages: vpm install http-client
        - Local .tar.gz files: vpm install ./packages/math-1.0.0.tar.gz
        - Python dependencies: vpm install-py requests numpy
        """
        # Check if installing from local file
        if package_name.endswith('.tar.gz') or package_name.endswith('.vakpkg'):
            return self.install_from_file(package_name, save)
        self._ensure_package_dir()
        
        # Load manifest
        manifest = self._load_manifest()
        if not manifest:
            print("❌ No vakya.json found. Run 'vpm init' first.")
            return False

        # Parse package@version syntax
        if '@' in package_name and version is None:
            package_name, version = package_name.split('@', 1)

        # Fetch package metadata from registry
        try:
            metadata = self._fetch_package_metadata(package_name, version)
        except Exception as e:
            print(f"❌ Failed to fetch metadata: {e}")
            return False

        # Check if already installed
        installed_version = self._get_installed_version(package_name)
        if installed_version:
            if installed_version == metadata.get('संस्करण'):
                print(f"ℹ️  {package_name}@{installed_version} already installed")
                if save:
                    self._add_dependency(package_name, metadata.get('संस्करण'))
                return True
            else:
                print(f"🔄 Upgrading {package_name} from {installed_version} to {metadata.get('संस्करण')}")

        # Download package
        package_path = os.path.join(self.package_dir, package_name)
        print(f"📥 Downloading {package_name}@{metadata.get('संस्करण')}...")

        try:
            self._download_package(package_name, metadata, package_path)
        except Exception as e:
            print(f"❌ Download failed: {e}")
            # Cleanup on failure
            if os.path.exists(package_path):
                shutil.rmtree(package_path)
            return False

        print(f"✅ Installed {package_name}@{metadata.get('संस्करण')}")

        # Save to manifest
        if save:
            self._add_dependency(package_name, metadata.get('संस्करण'))

        # Install dependencies
        dependencies = metadata.get('निर्भरताएँ', {})
        if dependencies:
            print(f"🔗 Installing {len(dependencies)} dependencies...")
            for dep_name, dep_version in dependencies.items():
                self.install(dep_name, dep_version, save=False)

        return True

    def install_from_file(self, file_path: str, save: bool = True) -> bool:
        """
        Install a package from a local .tar.gz or .vakpkg file.
        
        Args:
            file_path: Path to the package archive
            save: Whether to save to manifest
        
        Returns:
            True if successful
        """
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"📦 Installing from local package: {file_path}")
        self._ensure_package_dir()
        
        try:
            # Extract the package
            with tarfile.open(file_path, 'r:gz') as tar:
                # Get package name from archive
                members = tar.getmembers()
                if not members:
                    print("❌ Empty package archive")
                    return False
                
                # Root directory in archive
                root_dir = members[0].name.split('/')[0]
                if not root_dir:
                    print("❌ Invalid package archive layout")
                    return False
                
                # Extract to package directory
                extract_path = self._safe_join(self.package_dir, root_dir)
                
                # Remove existing installation
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)
                
                for member in members:
                    try:
                        self._safe_join(self.package_dir, member.name)
                    except ValueError as error:
                        print(f"❌ Unsafe package archive: {error}")
                        return False
                tar.extractall(self.package_dir)
            
            # Read package metadata
            manifest_file = os.path.join(extract_path, "vakya.json")
            if os.path.exists(manifest_file):
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    pkg_metadata = json.load(f)
                
                pkg_name = pkg_metadata.get('नाम', root_dir)
                pkg_version = pkg_metadata.get('संस्करण', 'unknown')
                
                print(f"✅ Installed {pkg_name}@{pkg_version}")
                self._sync_module_entrypoint(pkg_name, pkg_metadata, extract_path)
                
                # Save to project manifest
                if save:
                    self._add_dependency(pkg_name, pkg_version)
                
                # Install Python dependencies if specified
                py_deps = pkg_metadata.get('पायथन_निर्भरताएँ', [])
                if py_deps:
                    print(f"🐍 Installing {len(py_deps)} Python dependencies...")
                    self._install_python_deps(py_deps)
                
                # Install VakyaLang dependencies
                vak_deps = pkg_metadata.get('निर्भरताएँ', {})
                if vak_deps:
                    print(f"🔗 Installing {len(vak_deps)} VakyaLang dependencies...")
                    for dep_name, dep_version in vak_deps.items():
                        self.install(dep_name, dep_version, save=False)
                
                return True
            else:
                print(f"⚠️  Package extracted but no vakya.json found")
                return True
                
        except tarfile.TarError as e:
            print(f"❌ Failed to extract package: {e}")
            return False
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False

    def install_python_dep(self, package_name: str, version: str = None, save: bool = True) -> bool:
        """
        Install a Python dependency using pip.
        
        Args:
            package_name: Name of Python package
            version: Optional version constraint
            save: Whether to save to python_deps.json
        
        Returns:
            True if successful
        """
        spec = package_name
        if version:
            spec = f"{package_name}{version}"
        
        print(f"🐍 Installing Python package: {spec}...")
        
        try:
            # Run pip install
            cmd = [sys.executable, "-m", "pip", "install", spec]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print(f"✅ Installed Python package: {spec}")
            
            # Save to python_deps.json
            if save:
                self._save_python_dep(spec)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ pip install failed: {e.stderr}")
            return False
        except FileNotFoundError:
            print("❌ pip not found. Is Python installed?")
            return False

    def install_python_deps_from_file(self, requirements_file: str) -> bool:
        """Install Python dependencies from requirements.txt file"""
        if not os.path.exists(requirements_file):
            print(f"❌ File not found: {requirements_file}")
            return False
        
        print(f"🐍 Installing Python dependencies from {requirements_file}...")
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✅ Installed Python dependencies from {requirements_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ pip install failed: {e.stderr}")
            return False

    def _install_python_deps(self, dependencies: List[str]) -> bool:
        """Install list of Python dependencies"""
        for dep in dependencies:
            if not self.install_python_dep(dep, save=False):
                return False
        return True

    def _save_python_dep(self, package_spec: str):
        """Save Python dependency to python_deps.json"""
        deps_file = os.path.join(self.cwd, PYTHON_DEPS_MARKER)
        
        deps = []
        if os.path.exists(deps_file):
            with open(deps_file, 'r', encoding='utf-8') as f:
                deps = json.load(f)
        
        if package_spec not in deps:
            deps.append(package_spec)
            with open(deps_file, 'w', encoding='utf-8') as f:
                json.dump(deps, f, indent=2)

    def list_python_deps(self) -> List[str]:
        """List installed Python dependencies"""
        deps_file = os.path.join(self.cwd, PYTHON_DEPS_MARKER)
        if os.path.exists(deps_file):
            with open(deps_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def remove(self, package_name: str) -> bool:
        """Remove an installed package."""
        package_path = os.path.join(self.package_dir, package_name)
        alias_path = os.path.join(self.package_dir, f"{package_name}.vak")
        
        if not os.path.exists(package_path):
            print(f"❌ Package not found: {package_name}")
            return False
        
        shutil.rmtree(package_path)
        if os.path.exists(alias_path):
            os.remove(alias_path)
        print(f"✅ Removed {package_name}")
        
        # Remove from manifest
        self._remove_dependency(package_name)
        return True
    
    def list_installed(self) -> List[Dict[str, str]]:
        """List all installed packages."""
        if not os.path.exists(self.package_dir):
            return []
        
        packages = []
        for name in os.listdir(self.package_dir):
            pkg_path = os.path.join(self.package_dir, name)
            if os.path.isdir(pkg_path):
                manifest_file = os.path.join(pkg_path, "vakya.json")
                if os.path.exists(manifest_file):
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        packages.append({
                            'नाम': name,
                            'संस्करण': metadata.get('संस्करण', 'unknown')
                        })
        
        return packages
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for packages in the registry."""
        try:
            url = self.registry_url + "search.json?q=" + urllib.parse.quote(query)
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('packages', [])
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def info(self, package_name: str) -> Optional[Dict[str, Any]]:
        """Get package information."""
        # Check if installed
        installed_version = self._get_installed_version(package_name)
        if installed_version:
            pkg_path = os.path.join(self.package_dir, package_name)
            manifest_file = os.path.join(pkg_path, "vakya.json")
            if os.path.exists(manifest_file):
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    metadata['स्थिति'] = 'installed'
                    return metadata
        
        # Fetch from registry
        try:
            metadata = self._fetch_package_metadata(package_name)
            metadata['स्थिति'] = 'registry'
            return metadata
        except Exception as e:
            print(f"❌ Package not found: {package_name}")
            return None
    
    def _load_manifest(self) -> Optional[Dict[str, Any]]:
        """Load vakya.json manifest."""
        if not os.path.exists(self.manifest_path):
            return None
        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid vakya.json: {error}") from error
    
    def _fetch_package_metadata(self, package_name: str, version: str = None) -> Dict[str, Any]:
        """Fetch package metadata from registry."""
        # Try local registry file first (offline mode)
        registry_file = os.path.join(self.package_dir, "registry.json")
        if os.path.exists(registry_file):
            with open(registry_file, 'r', encoding='utf-8') as f:
                registry = json.load(f)
                if package_name in registry:
                    pkg_data = registry[package_name]
                    if version is None or pkg_data.get('संस्करण') == version:
                        return pkg_data
        
        # Fetch from remote registry
        try:
            url = f"{self.registry_url}packages/{package_name}/vakya.json"
            req = urllib.request.Request(url, headers={'User-Agent': 'VakPack/1.0'})
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Package not found: {package_name}")
            raise
        except urllib.error.URLError as e:
            # Offline mode - check if package exists in cache
            raise Exception(f"Registry unavailable: {e.reason}")
    
    def _download_package(self, package_name: str, metadata: Dict, package_path: str):
        """Download package files."""
        self._ensure_package_dir()
        os.makedirs(package_path, exist_ok=True)
        
        # Download main package file
        files = metadata.get('फाइलें', [f"{package_name}.vak"])
        
        for file_path in files:
            try:
                normalized = self._safe_relative_path(file_path)
                url = f"{self.registry_url}packages/{package_name}/{file_path}"
                req = urllib.request.Request(url, headers={'User-Agent': 'VakPack/1.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                
                dest_path = self._safe_join(package_path, normalized)
                parent_dir = os.path.dirname(dest_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"⚠️  Failed to download {file_path}: {e}")
        
        # Save metadata
        metadata_path = os.path.join(package_path, "vakya.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        self._sync_module_entrypoint(package_name, metadata, package_path)
    
    def _get_installed_version(self, package_name: str) -> Optional[str]:
        """Get version of installed package."""
        pkg_path = os.path.join(self.package_dir, package_name)
        manifest_file = os.path.join(pkg_path, "vakya.json")
        
        if os.path.exists(manifest_file):
            with open(manifest_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('संस्करण')
        
        return None
    
    def _add_dependency(self, package_name: str, version: str):
        """Add dependency to manifest."""
        manifest = self._load_manifest()
        if not manifest:
            return
        
        if 'निर्भरताएँ' not in manifest:
            manifest['निर्भरताएँ'] = {}
        
        manifest['निर्भरताएँ'][package_name] = version
        
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def _remove_dependency(self, package_name: str):
        """Remove dependency from manifest."""
        manifest = self._load_manifest()
        if not manifest:
            return
        
        if 'निर्भरताएँ' in manifest:
            manifest['निर्भरताएँ'].pop(package_name, None)
        
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='VakPack - VakyaLang Package Manager',
        prog='vpm',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vpm install http-client           Install from registry
  vpm install ./pkg.tar.gz          Install from local file
  vpm install-py requests numpy     Install Python packages
  vpm bundle --output ./packages    Create library bundles
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # init command
    init_parser = subparsers.add_parser('init', help='Initialize new project')

    # install command
    install_parser = subparsers.add_parser('install', help='Install package')
    install_parser.add_argument('package', help='Package name or file path')
    install_parser.add_argument('--no-save', action='store_true', help='Don\'t save to vakya.json')

    # install-py command (NEW)
    install_py_parser = subparsers.add_parser('install-py', help='Install Python dependency')
    install_py_parser.add_argument('package', nargs='+', help='Python package name(s)')
    install_py_parser.add_argument('--version', '-v', help='Version constraint')
    install_py_parser.add_argument('--no-save', action='store_true', help='Don\'t save')

    # remove command
    remove_parser = subparsers.add_parser('remove', help='Remove package')
    remove_parser.add_argument('package', help='Package name')

    # list command
    list_parser = subparsers.add_parser('list', help='List installed packages')
    list_parser.add_argument('--python', action='store_true', help='List Python dependencies')

    # search command
    search_parser = subparsers.add_parser('search', help='Search packages')
    search_parser.add_argument('query', help='Search query')

    # info command
    info_parser = subparsers.add_parser('info', help='Package information')
    info_parser.add_argument('package', help='Package name')

    # bundle command (NEW)
    bundle_parser = subparsers.add_parser('bundle', help='Create library bundles')
    bundle_parser.add_argument('--lib', '-l', help='Specific library to bundle')
    bundle_parser.add_argument('--version', '-v', default='1.0.0', help='Version string')
    bundle_parser.add_argument('--output', '-o', help='Output directory')
    bundle_parser.add_argument('--all', action='store_true', help='Bundle all libraries')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    vpm = VakPackageManager()

    if args.command == 'init':
        success = vpm.init()
    elif args.command == 'install':
        success = vpm.install(args.package, save=not args.no_save)
    elif args.command == 'install-py':
        success = True
        for pkg in args.package:
            if not vpm.install_python_dep(pkg, args.version, save=not args.no_save):
                success = False
    elif args.command == 'remove':
        success = vpm.remove(args.package)
    elif args.command == 'list':
        if args.python:
            # List Python dependencies
            py_deps = vpm.list_python_deps()
            if py_deps:
                print(f"🐍 Python dependencies:")
                for dep in py_deps:
                    print(f"  {dep}")
            else:
                print("No Python dependencies")
        else:
            # List VakyaLang packages
            packages = vpm.list_installed()
            if packages:
                print(f"📦 Installed packages in {PACKAGE_DIR}/:")
                for pkg in packages:
                    print(f"  {pkg['नाम']}@{pkg['संस्करण']}")
            else:
                print("No packages installed")
        success = True
    elif args.command == 'search':
        results = vpm.search(args.query)
        if results:
            print(f"🔍 Search results for '{args.query}':")
            for pkg in results:
                print(f"  {pkg.get('नाम')} - {pkg.get('विवरण', '')}")
        else:
            print("No packages found")
        success = True
    elif args.command == 'info':
        info = vpm.info(args.package)
        if info:
            print(f"📦 {info.get('नाम')}@{info.get('संस्करण')}")
            print(f"   {info.get('विवरण', '')}")
            print(f"   Status: {info.get('स्थिति', 'unknown')}")
            if 'निर्भरताएँ' in info:
                print(f"   Dependencies: {info['निर्भरताएँ']}")
            if 'पायथन_निर्भरताएँ' in info:
                print(f"   Python Dependencies: {info['पायथन_निर्भरताएँ']}")
        success = True
    elif args.command == 'bundle':
        # Import packager
        repo_root = os.path.dirname(os.path.abspath(__file__))
        dev_root = os.path.join(repo_root, "dev")
        sys.path.insert(0, repo_root)
        if os.path.isdir(dev_root):
            sys.path.insert(0, dev_root)
        from package_lib import VakPackageBuilder
        
        builder = VakPackageBuilder(output_dir=args.output)
        
        if args.lib:
            success = builder.package_single(args.lib, args.version) is not None
        elif args.all:
            success = len(builder.package_all(args.version)) > 0
        else:
            # Default: create stdlib bundle
            success = builder.create_stdlib_bundle(args.version) is not None
    else:
        success = False

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
