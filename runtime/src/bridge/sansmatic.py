# सान्समैटिक सेतु — Sansmatic Bridge for वाक् Language
# Registers the proof engine as native वाक् built-in functions.
# © 2026 Raj Mitra

import sys, os
unified_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if unified_root not in sys.path:
    sys.path.insert(0, unified_root)

from sansmatic.src.engine import SansmaticEngine, ProofError
from ..errors import VakRuntimeError


# One global engine per वाक् program run
_engine = SansmaticEngine(verbose=True)


def register_sansmatic_bridge(globals_env):
    """Register all Sansmatic proof functions into वाक् global scope."""

    from ..interpreter import BuiltinFunction

    def _define(args, kwargs):
        """परिभाषय(नाम, गुण_सूची) — Define a concept with properties."""
        if len(args) < 2:
            raise VakRuntimeError("परिभाषय: नाम और गुण_सूची चाहिए")
        name = str(args[0])
        props = args[1]
        return _engine.define(name, props)

    def _assert(args, kwargs):
        """दावा(इकाई, संबंध, गुण) — Assert a fact is provable."""
        if len(args) < 3:
            raise VakRuntimeError("दावा: इकाई, संबंध, गुण चाहिए")
        try:
            proof_id = str(args[3]) if len(args) > 3 else None
            return _engine.assert_fact(str(args[0]), str(args[1]), str(args[2]), proof_id)
        except ProofError as e:
            raise VakRuntimeError(str(e))

    def _rule(args, kwargs):
        """नियम(इकाई1, संबंध1, गुण1, इकाई2, संबंध2, गुण2)"""
        if len(args) < 6:
            raise VakRuntimeError("नियम: दो तथ्य चाहिए (6 तर्क)")
        premise    = (str(args[0]), str(args[1]), str(args[2]))
        conclusion = (str(args[3]), str(args[4]), str(args[5]))
        return _engine.rule(premise, conclusion)

    def _evaluate(args, kwargs):
        """मूल्यांकन(इकाई, संबंध, गुण) — Is this derivable?"""
        if len(args) < 3:
            raise VakRuntimeError("मूल्यांकन: इकाई, संबंध, गुण चाहिए")
        return _engine.evaluate(str(args[0]), str(args[1]), str(args[2]))

    def _is_provable(args, kwargs):
        """सिद्ध_है(इकाई, संबंध, गुण) → सत्य/असत्य"""
        if len(args) < 3:
            return False
        return _engine.is_provable(str(args[0]), str(args[1]), str(args[2]))

    def _proof_log(args, kwargs):
        """प्रमाण_लॉग() → सूची — Return full proof history."""
        return _engine.get_log()

    def _reset_engine(args, kwargs):
        """प्रमाण_रीसेट() — Clear all facts, rules, definitions."""
        _engine.reset()
        return None

    sansmatic_builtins = {
        "परिभाषय":      _define,       # define
        "दावा":         _assert,       # assert
        "नियम":         _rule,         # rule
        "मूल्यांकन":    _evaluate,     # evaluate
        "सिद्ध_है":     _is_provable,  # is_provable → bool
        "प्रमाण_लॉग":   _proof_log,    # get proof log
        "प्रमाण_रीसेट": _reset_engine, # reset engine
    }

    for name, fn in sansmatic_builtins.items():
        globals_env.define(name, BuiltinFunction(name, fn))
