# VakyaLang (वाक्) — Copyright (c) 2026 Raj Mitra. All Rights Reserved.
# Original author: Raj Mitra (Visionary RM)
# Licensed under GNU AGPL v3.0 — see LICENSE and NOTICE.
# Any use, modification, or derivative work must preserve this header
# and include the NOTICE file. https://github.com/Sansmatic-z/VakyaLang
# वाक् भाषा - प्रणाली सेतु (System Bridge)
# Vak Language - File I/O and OS Bridge

import os
import shutil
import sys
import platform
import subprocess

from ..errors import VakRuntimeError, VakTypeError

def register_system_bridge(globals_env):
    """Register all system-level built-ins."""

    # ── File I/O ─────────────────────────────────────────────────────────────

    def _file_read(args, kwargs):
        """पठन(पथ) -> str"""
        if not args: raise VakTypeError("पठन: पथ (path) चाहिए")
        path = str(args[0])
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise VakRuntimeError(f"पठन विफल: {e}")

    def _file_write(args, kwargs):
        """लेखन(पथ, डेटा, मोड='w') -> null"""
        if len(args) < 2: raise VakTypeError("लेखन: पथ और डेटा चाहिए")
        path = str(args[0])
        data = str(args[1])
        mode = str(args[2]) if len(args) > 2 else 'w'
        try:
            with open(path, mode, encoding='utf-8') as f:
                f.write(data)
            return None
        except Exception as e:
            raise VakRuntimeError(f"लेखन विफल: {e}")

    def _file_exists(args, kwargs):
        """अस्तित्व(पथ) -> bool"""
        if not args: return False
        return os.path.exists(str(args[0]))

    def _file_remove(args, kwargs):
        """मिटाओ(पथ) -> null"""
        if not args: return None
        path = str(args[0])
        if os.path.exists(path):
            os.remove(path)
        return None

    # ── Directory Operations ─────────────────────────────────────────────────

    def _list_dir(args, kwargs):
        """सूची_निर्देशिका(पथ='.') -> list"""
        path = str(args[0]) if args else '.'
        try:
            return os.listdir(path)
        except Exception as e:
            raise VakRuntimeError(f"सूची_निर्देशिका विफल: {e}")

    def _make_dir(args, kwargs):
        """बनाओ_निर्देशिका(पथ) -> null"""
        if not args: return None
        os.makedirs(str(args[0]), exist_ok=True)
        return None

    # ── OS & Process ─────────────────────────────────────────────────────────

    def _get_env(args, kwargs):
        """परिवेश_प्राप्त(कुंजी) -> str"""
        if not args: return None
        return os.environ.get(str(args[0]))

    def _set_env(args, kwargs):
        """परिवेश_सेट(कुंजी, मान) -> null"""
        if len(args) < 2: return None
        os.environ[str(args[0])] = str(args[1])
        return None

    def _system_shell(args, kwargs):
        """प्रणाली_कमांड(कमांड) -> int"""
        if not args: return 1
        return os.system(str(args[0]))

    def _get_platform(args, kwargs):
        """मंच() -> str"""
        return platform.system()

    # ── Registration ─────────────────────────────────────────────────────────
    
    system_builtins = {
        "पठन":               _file_read,     # read
        "लेखन":               _file_write,    # write
        "अस्तित्व":           _file_exists,   # exists
        "मिटाओ":              _file_remove,   # remove
        "सूची_निर्देशिका":    _list_dir,      # listdir
        "बनाओ_निर्देशिका":    _make_dir,      # mkdir
        "परिवेश_प्राप्त":      _get_env,       # getenv
        "परिवेश_सेट":        _set_env,       # setenv
        "प्रणाली_कमांड":      _system_shell,  # system (shell)
        "मंच":                _get_platform,  # platform
        "कार्य_निर्देशिका":    lambda a,k: os.getcwd(), # getcwd
    }

    from ..interpreter import BuiltinFunction
    for name, fn in system_builtins.items():
        globals_env.define(name, BuiltinFunction(name, fn))

