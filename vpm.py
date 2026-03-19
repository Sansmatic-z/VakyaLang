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
from pathlib import Path
from typing import Dict, List, Optional, Any

# Default registry URL (can be overridden)
DEFAULT_REGISTRY = "https://raw.githubusercontent.com/Sansmatic-z/vak-packages/main/"

# Package directory name (like node_modules)
PACKAGE_DIR = "वाक्_ग्रंथालय"


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
        self.registry_url = DEFAULT_REGISTRY
    
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
        os.makedirs(self.package_dir, exist_ok=True)
        
        print(f"✅ Initialized vakya.json in {self.cwd}")
        print(f"📦 Package directory: {PACKAGE_DIR}/")
        return True
    
    def install(self, package_name: str, version: str = None, save: bool = True) -> bool:
        """
        Install a package from the registry.
        
        Downloads package files and places them in वाक्_ग्रंथालय/<package-name>/
        """
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
    
    def remove(self, package_name: str) -> bool:
        """Remove an installed package."""
        package_path = os.path.join(self.package_dir, package_name)
        
        if not os.path.exists(package_path):
            print(f"❌ Package not found: {package_name}")
            return False
        
        shutil.rmtree(package_path)
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
        
        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
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
        os.makedirs(package_path, exist_ok=True)
        
        # Download main package file
        files = metadata.get('फाइलें', [f"{package_name}.vak"])
        
        for file_path in files:
            try:
                url = f"{self.registry_url}packages/{package_name}/{file_path}"
                req = urllib.request.Request(url, headers={'User-Agent': 'VakPack/1.0'})
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                
                dest_path = os.path.join(package_path, file_path)
                os.makedirs(os.path.dirname(dest_path) if os.path.dirname(dest_path) else '.', exist_ok=True)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
            except Exception as e:
                print(f"⚠️  Failed to download {file_path}: {e}")
        
        # Save metadata
        metadata_path = os.path.join(package_path, "vakya.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
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
        prog='vpm'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize new project')
    
    # install command
    install_parser = subparsers.add_parser('install', help='Install package')
    install_parser.add_argument('package', help='Package name (e.g., http-client@1.0.0)')
    install_parser.add_argument('--no-save', action='store_true', help='Don\'t save to vakya.json')
    
    # remove command
    remove_parser = subparsers.add_parser('remove', help='Remove package')
    remove_parser.add_argument('package', help='Package name')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List installed packages')
    
    # search command
    search_parser = subparsers.add_parser('search', help='Search packages')
    search_parser.add_argument('query', help='Search query')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Package information')
    info_parser.add_argument('package', help='Package name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    vpm = VakPackageManager()
    
    if args.command == 'init':
        success = vpm.init()
    elif args.command == 'install':
        success = vpm.install(args.package, save=not args.no_save)
    elif args.command == 'remove':
        success = vpm.remove(args.package)
    elif args.command == 'list':
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
        success = True
    else:
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
