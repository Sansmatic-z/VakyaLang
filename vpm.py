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
import inspect
import importlib.util
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from runtime.src.audit import emit_audit_event

# Default registry URL (can be overridden)
DEFAULT_REGISTRY = "https://raw.githubusercontent.com/Sansmatic-z/vak-packages/main/"

# Package directory name (like node_modules)
PACKAGE_DIR = "वाक्_ग्रंथालय"

# Python dependencies marker
PYTHON_DEPS_MARKER = ".python_deps.json"
LOCKFILE_NAME = "vakya.lock.json"
VPM_CACHE_ROOT = ".vak_cache"
VPM_CACHE_NAMESPACE = "vpm"
MAX_ARCHIVE_MEMBERS = 512
MAX_ARCHIVE_TOTAL_SIZE = 64 * 1024 * 1024
MAX_ARCHIVE_MEMBER_SIZE = 16 * 1024 * 1024


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


def _load_package_builder(repo_root: str):
    package_builder_path = Path(repo_root) / "dev" / "package_lib.py"
    spec = importlib.util.spec_from_file_location("vak_dev_package_lib", package_builder_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load package builder from {package_builder_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VakPackageBuilder


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
        self.lockfile_path = os.path.join(self.cwd, LOCKFILE_NAME)
        self.registry_url = os.getenv("VPM_REGISTRY", DEFAULT_REGISTRY)
        if not self.registry_url.endswith("/"):
            self.registry_url += "/"

    def _ensure_package_dir(self) -> None:
        os.makedirs(self.package_dir, exist_ok=True)

    def _validate_package_name(self, package_name: str) -> str:
        text = package_name.strip()
        if not text:
            raise ValueError("Empty package name")
        if any(marker in text for marker in ("/", "\\", ":")):
            raise ValueError(f"Unsafe package name: {package_name}")
        if text in {".", ".."} or ".." in text.split("."):
            raise ValueError(f"Unsafe package name: {package_name}")
        return text

    def _cache_root(self) -> str:
        return os.path.join(self.cwd, VPM_CACHE_ROOT, VPM_CACHE_NAMESPACE)

    def _ensure_cache_dir(self) -> None:
        os.makedirs(self._cache_root(), exist_ok=True)

    def _metadata_cache_path(self, package_name: str, version: str | None = None) -> str:
        version_label = version or "latest"
        safe_version = version_label.replace("/", "_").replace("\\", "_")
        return os.path.join(self._cache_root(), "metadata", f"{package_name}@{safe_version}.json")

    def _archive_cache_path(self, file_path: str) -> str:
        with open(file_path, "rb") as source_file:
            digest = hashlib.sha256(source_file.read()).hexdigest()[:16]
        filename = os.path.basename(file_path)
        return os.path.join(self._cache_root(), "archives", f"{digest}-{filename}")

    def _hash_file(self, file_path: str) -> str:
        digest = hashlib.sha256()
        with open(file_path, "rb") as source_file:
            while True:
                chunk = source_file.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    def _package_lock_entry(self, package_name: str) -> Optional[Dict[str, Any]]:
        package_path = os.path.join(self.package_dir, package_name)
        manifest_path = os.path.join(package_path, "vakya.json")
        if not os.path.exists(manifest_path):
            return None
        with open(manifest_path, 'r', encoding='utf-8') as manifest_file:
            metadata = json.load(manifest_file)
        files: List[Dict[str, Any]] = []
        for relative_path in sorted(metadata.get('फाइलें', [])):
            try:
                normalized = self._safe_relative_path(relative_path)
                resolved = self._safe_join(package_path, normalized)
            except ValueError:
                continue
            if not os.path.exists(resolved):
                continue
            files.append(
                {
                    "path": normalized,
                    "sha256": self._hash_file(resolved),
                    "size": os.path.getsize(resolved),
                }
            )
        entry = {
            "नाम": package_name,
            "संस्करण": metadata.get('संस्करण', 'unknown'),
            "manifest_sha256": self._hash_file(manifest_path),
            "files": files,
        }
        python_deps = metadata.get('पायथन_निर्भरताएँ', [])
        if python_deps:
            entry["पायथन_निर्भरताएँ"] = list(python_deps)
        dependencies = metadata.get('निर्भरताएँ', {})
        if dependencies:
            entry["निर्भरताएँ"] = dict(dependencies)
        return entry

    def _write_json(self, path: str, payload: Any) -> None:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as target:
            json.dump(payload, target, indent=2, ensure_ascii=False)

    def _cache_metadata(self, package_name: str, metadata: Dict[str, Any], version: str | None = None) -> None:
        self._ensure_cache_dir()
        self._write_json(self._metadata_cache_path(package_name, version), metadata)

    def _load_cached_metadata(self, package_name: str, version: str | None = None) -> Optional[Dict[str, Any]]:
        cache_path = self._metadata_cache_path(package_name, version)
        if not os.path.exists(cache_path):
            return None
        with open(cache_path, 'r', encoding='utf-8') as cached_file:
            return json.load(cached_file)

    def _cache_archive(self, file_path: str) -> Optional[str]:
        if not os.path.exists(file_path):
            return None
        self._ensure_cache_dir()
        cache_path = self._archive_cache_path(file_path)
        parent = os.path.dirname(cache_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        shutil.copy2(file_path, cache_path)
        return cache_path

    def _lockfile_payload(self) -> Dict[str, Any]:
        manifest = self._load_manifest() or {}
        packages = []
        for package in self.list_installed():
            entry = self._package_lock_entry(package["नाम"])
            if entry is None:
                entry = dict(package)
            packages.append(entry)
        return {
            "version": 1,
            "project": manifest.get("नाम", os.path.basename(self.cwd) or "अज्ञात-परियोजना"),
            "registry": self.registry_url,
            "dependencies": dict(manifest.get("निर्भरताएँ", {})),
            "packages": sorted(packages, key=lambda item: item.get("नाम", "")),
            "python_dependencies": self.list_python_deps(),
            "cache": self.cache_info(),
        }

    def write_lockfile(self) -> Dict[str, Any]:
        payload = self._lockfile_payload()
        self._write_json(self.lockfile_path, payload)
        emit_audit_event("vak.package.lock.write", self.lockfile_path, len(payload.get("packages", [])))
        return payload

    def cache_info(self) -> Dict[str, Any]:
        cache_root = self._cache_root()
        metadata_files = 0
        archive_files = 0
        size_bytes = 0
        if os.path.exists(cache_root):
            for root, _, files in os.walk(cache_root):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    try:
                        size_bytes += os.path.getsize(file_path)
                    except OSError:
                        continue
                    if root.endswith("metadata"):
                        metadata_files += 1
                    elif root.endswith("archives"):
                        archive_files += 1
        return {
            "root": cache_root,
            "metadata_files": metadata_files,
            "archive_files": archive_files,
            "size_bytes": size_bytes,
        }

    def clear_cache(self) -> bool:
        cache_root = self._cache_root()
        if not os.path.exists(cache_root):
            return True
        shutil.rmtree(cache_root)
        emit_audit_event("vak.package.cache.clear", cache_root)
        return True

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
        self.write_lockfile()
        
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

        try:
            package_name = self._validate_package_name(package_name)
        except ValueError as error:
            print(f"❌ {error}")
            emit_audit_event("vak.package.install.error", str(package_name), str(error))
            return False

        emit_audit_event("vak.package.install.start", package_name, version or "latest")
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
            emit_audit_event("vak.package.install.error", package_name, str(e))
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
            emit_audit_event("vak.package.install.error", package_name, str(e))
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

        self.write_lockfile()
        emit_audit_event("vak.package.install.complete", package_name, metadata.get('संस्करण'))

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
        emit_audit_event("vak.package.install_file.start", file_path)
        self._ensure_package_dir()
        
        try:
            self._cache_archive(file_path)
            # Extract the package
            with tarfile.open(file_path, 'r:gz') as tar:
                # Get package name from archive
                members = tar.getmembers()
                if not members:
                    print("❌ Empty package archive")
                    emit_audit_event("vak.package.install_file.error", file_path, "empty")
                    return False

                safe_members = []
                roots = set()
                total_size = 0
                if len(members) > MAX_ARCHIVE_MEMBERS:
                    print("❌ Package archive exceeds member limit")
                    emit_audit_event("vak.package.install_file.error", file_path, "member_limit")
                    return False
                for member in members:
                    if member.issym() or member.islnk() or member.isdev():
                        print("❌ Unsafe package archive: links and device files are not allowed")
                        emit_audit_event("vak.package.install_file.error", file_path, "unsafe_member")
                        return False
                    if member.size > MAX_ARCHIVE_MEMBER_SIZE:
                        print("❌ Package archive member too large")
                        emit_audit_event("vak.package.install_file.error", file_path, "member_too_large")
                        return False
                    total_size += max(member.size, 0)
                    if total_size > MAX_ARCHIVE_TOTAL_SIZE:
                        print("❌ Package archive exceeds total size limit")
                        emit_audit_event("vak.package.install_file.error", file_path, "archive_too_large")
                        return False
                    try:
                        normalized = self._safe_relative_path(member.name)
                    except ValueError as error:
                        print(f"❌ Unsafe package archive: {error}")
                        emit_audit_event("vak.package.install_file.error", file_path, str(error))
                        return False
                    roots.add(normalized.split('/')[0])
                    safe_members.append(member)

                if len(roots) != 1:
                    print("❌ Invalid package archive layout")
                    emit_audit_event("vak.package.install_file.error", file_path, "invalid_layout")
                    return False

                # Root directory in archive
                root_dir = next(iter(roots))
                if not root_dir:
                    print("❌ Invalid package archive layout")
                    emit_audit_event("vak.package.install_file.error", file_path, "empty_root")
                    return False

                # Extract to package directory
                extract_path = self._safe_join(self.package_dir, root_dir)

                # Remove existing installation
                if os.path.exists(extract_path):
                    shutil.rmtree(extract_path)

                if not any(
                    self._safe_relative_path(member.name) == f"{root_dir}/vakya.json"
                    for member in safe_members
                ):
                    print("❌ Package archive missing vakya.json")
                    emit_audit_event("vak.package.install_file.error", file_path, "missing_manifest")
                    return False
                extract_kwargs = {"path": self.package_dir}
                if "filter" in inspect.signature(tar.extractall).parameters:
                    extract_kwargs["filter"] = "data"
                tar.extractall(**extract_kwargs)
            
            # Read package metadata
            manifest_file = os.path.join(extract_path, "vakya.json")
            if os.path.exists(manifest_file):
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    pkg_metadata = json.load(f)
                
                pkg_name = pkg_metadata.get('नाम', root_dir)
                try:
                    pkg_name = self._validate_package_name(pkg_name)
                except ValueError as error:
                    print(f"❌ {error}")
                    emit_audit_event("vak.package.install_file.error", file_path, str(error))
                    return False
                pkg_version = pkg_metadata.get('संस्करण', 'unknown')
                pkg_files = [self._safe_relative_path(path) for path in pkg_metadata.get('फाइलें', [])]
                for relative_path in pkg_files:
                    resolved = self._safe_join(extract_path, relative_path)
                    if not os.path.exists(resolved):
                        print(f"❌ Package manifest references missing file: {relative_path}")
                        emit_audit_event("vak.package.install_file.error", file_path, f"missing_file:{relative_path}")
                        return False
                
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
                self.write_lockfile()
                emit_audit_event("vak.package.install_file.complete", file_path, pkg_name, pkg_version)
                return True
            else:
                print(f"❌ Package archive missing vakya.json")
                emit_audit_event("vak.package.install_file.error", file_path, "missing_manifest")
                return False
                
        except tarfile.TarError as e:
            print(f"❌ Failed to extract package: {e}")
            emit_audit_event("vak.package.install_file.error", file_path, str(e))
            return False
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            emit_audit_event("vak.package.install_file.error", file_path, str(e))
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
        emit_audit_event("vak.package.python.install.start", spec)
        
        try:
            # Run pip install
            cmd = [sys.executable, "-m", "pip", "install", spec]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            print(f"✅ Installed Python package: {spec}")
            
            # Save to python_deps.json
            if save:
                self._save_python_dep(spec)
                self.write_lockfile()
            emit_audit_event("vak.package.python.install.complete", spec)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ pip install failed: {e.stderr}")
            emit_audit_event("vak.package.python.install.error", spec, e.stderr)
            return False
        except FileNotFoundError:
            print("❌ pip not found. Is Python installed?")
            emit_audit_event("vak.package.python.install.error", spec, "pip not found")
            return False

    def install_python_deps_from_file(self, requirements_file: str) -> bool:
        """Install Python dependencies from requirements.txt file"""
        if not os.path.exists(requirements_file):
            print(f"❌ File not found: {requirements_file}")
            emit_audit_event("vak.package.python.install_file.error", requirements_file, "missing_file")
            return False
        
        print(f"🐍 Installing Python dependencies from {requirements_file}...")
        emit_audit_event("vak.package.python.install_file.start", requirements_file)
        
        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_file]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.write_lockfile()
            print(f"✅ Installed Python dependencies from {requirements_file}")
            emit_audit_event("vak.package.python.install_file.complete", requirements_file)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ pip install failed: {e.stderr}")
            emit_audit_event("vak.package.python.install_file.error", requirements_file, e.stderr)
            return False

    def _install_python_deps(self, dependencies: List[str]) -> bool:
        """Install list of Python dependencies"""
        emit_audit_event("vak.package.python.install_batch.start", tuple(dependencies))
        for dep in dependencies:
            if not self.install_python_dep(dep, save=False):
                emit_audit_event("vak.package.python.install_batch.error", dep)
                return False
        emit_audit_event("vak.package.python.install_batch.complete", tuple(dependencies))
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

    def remove_python_dep(self, package_name: str) -> bool:
        """Remove a Python dependency marker by package name."""
        deps = self.list_python_deps()
        remaining = []
        removed = False
        target = package_name.strip().lower()
        for spec in deps:
            name = re.split(r'[<>=!~ ]+', spec, maxsplit=1)[0].strip().lower()
            if name == target:
                removed = True
                continue
            remaining.append(spec)
        if not removed:
            print(f"❌ Python dependency not found: {package_name}")
            return False
        deps_file = os.path.join(self.cwd, PYTHON_DEPS_MARKER)
        with open(deps_file, 'w', encoding='utf-8') as f:
            json.dump(remaining, f, indent=2)
        self.write_lockfile()
        print(f"✅ Removed Python dependency: {package_name}")
        emit_audit_event("vak.package.python.remove", package_name)
        return True
    
    def remove(self, package_name: str) -> bool:
        """Remove an installed package."""
        try:
            package_name = self._validate_package_name(package_name)
        except ValueError as error:
            print(f"❌ {error}")
            emit_audit_event("vak.package.remove.error", str(package_name), str(error))
            return False
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
        self.write_lockfile()
        emit_audit_event("vak.package.remove", package_name)
        return True

    def update(self, package_name: str | None = None) -> bool:
        """Refresh one dependency or all declared dependencies."""
        emit_audit_event("vak.package.update.start", package_name or "<all>")
        manifest = self._load_manifest()
        if not manifest:
            print("❌ No vakya.json found. Run 'vpm init' first.")
            emit_audit_event("vak.package.update.error", package_name or "<all>", "missing_manifest")
            return False
        dependencies = manifest.get('निर्भरताएँ', {})
        if package_name:
            targets = [package_name]
        else:
            targets = sorted(dependencies.keys())
        if not targets:
            print("ℹ️  No VakyaLang dependencies to update")
            self.write_lockfile()
            emit_audit_event("vak.package.update.complete", "<none>")
            return True
        success = True
        for name in targets:
            if not self.install(name, save=True):
                success = False
        if success:
            self.write_lockfile()
            emit_audit_event("vak.package.update.complete", package_name or "<all>")
        else:
            emit_audit_event("vak.package.update.error", package_name or "<all>", "install_failed")
        return success
    
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
                metadata = json.loads(response.read().decode('utf-8'))
                self._cache_metadata(package_name, metadata, version)
                return metadata
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Exception(f"Package not found: {package_name}")
            raise
        except urllib.error.URLError as e:
            # Offline mode - check if package exists in cache
            cached = self._load_cached_metadata(package_name, version)
            if cached is not None:
                return cached
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

    remove_py_parser = subparsers.add_parser('remove-py', help='Remove Python dependency marker')
    remove_py_parser.add_argument('package', help='Python package name')

    update_parser = subparsers.add_parser('update', help='Update installed dependencies')
    update_parser.add_argument('package', nargs='?', help='Optional package name')

    # list command
    list_parser = subparsers.add_parser('list', help='List installed packages')
    list_parser.add_argument('--python', action='store_true', help='List Python dependencies')

    lock_parser = subparsers.add_parser('lock', help='Write vakya.lock.json')

    cache_parser = subparsers.add_parser('cache', help='Inspect or clear VPM cache')
    cache_parser.add_argument('action', nargs='?', default='info', choices=['info', 'clear'])

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
    elif args.command == 'remove-py':
        success = vpm.remove_python_dep(args.package)
    elif args.command == 'update':
        success = vpm.update(args.package)
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
    elif args.command == 'lock':
        payload = vpm.write_lockfile()
        print(f"🔒 Lockfile written: {vpm.lockfile_path}")
        print(f"   packages={len(payload['packages'])}, python={len(payload['python_dependencies'])}")
        success = True
    elif args.command == 'cache':
        if args.action == 'clear':
            success = vpm.clear_cache()
            print("🧹 Cache cleared")
        else:
            info = vpm.cache_info()
            print(f"📦 Cache root: {info['root']}")
            print(f"   metadata_files={info['metadata_files']}")
            print(f"   archive_files={info['archive_files']}")
            print(f"   size_bytes={info['size_bytes']}")
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
        repo_root = os.path.dirname(os.path.abspath(__file__))
        VakPackageBuilder = _load_package_builder(repo_root)
        builder = VakPackageBuilder(
            stdlib_dir=os.path.join(repo_root, "runtime", "stdlib"),
            output_dir=args.output,
        )
        emit_audit_event("vak.package.bundle.start", args.lib or "<stdlib-bundle>", args.output)
        
        if args.lib:
            success = builder.package_single(args.lib, args.version) is not None
        elif args.all:
            success = len(builder.package_all(args.version)) > 0
        else:
            # Default: create stdlib bundle
            success = builder.create_stdlib_bundle(args.version) is not None
        emit_audit_event("vak.package.bundle.complete", args.lib or "<stdlib-bundle>", bool(success))
    else:
        success = False

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
