# सान्समैटिक सेतु — Sansmatic Bridge for वाक् Language
# Registers the proof engine as native वाक् built-in functions.
# © 2026 Raj Mitra

import sys, os
unified_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if unified_root not in sys.path:
    sys.path.insert(0, unified_root)

from sansmatic.src.config import SansmaticSettings
from sansmatic.src.engine import SansmaticEngine, ProofError
from ..errors import VakRuntimeError


# One global engine per वाक् program run
_engine = SansmaticEngine(verbose=True, settings=SansmaticSettings.from_env())


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

    def _backward_provable(args, kwargs):
        """पश्च_सिद्ध_है(इकाई, संबंध, गुण) → सत्य/असत्य"""
        if len(args) < 3:
            return False
        return _engine.backward_chain((str(args[0]), str(args[1]), str(args[2])))

    def _proof_log(args, kwargs):
        """प्रमाण_लॉग() → सूची — Return full proof history."""
        return _engine.get_log()

    def _proof_summary(args, kwargs):
        """प्रमाण_सारांश() → शब्दकोश — Return proof-engine summary."""
        return _engine.summary()

    def _proof_snapshot(args, kwargs):
        """प्रमाण_स्नैपशॉट() → शब्दकोश — Capture proof-engine state."""
        return _engine.snapshot()

    def _proof_restore(args, kwargs):
        """प्रमाण_पुनर्स्थापय([state]) → सत्य/असत्य — Restore saved proof-engine state."""
        state = args[0] if args else None
        return _engine.restore(state)

    def _proof_trace(args, kwargs):
        """प्रमाण_अनुक्रम([limit]) → सूची — Return structured proof trace."""
        limit = int(args[0]) if args else None
        return _engine.trace(limit=limit)

    def _proof_tree(args, kwargs):
        """प्रमाण_वृक्ष(इकाई, संबंध, गुण) → शब्दकोश — Return proof tree."""
        if len(args) < 3:
            raise VakRuntimeError("प्रमाण_वृक्ष: इकाई, संबंध, गुण चाहिए")
        return _engine.proof_tree((str(args[0]), str(args[1]), str(args[2])))

    def _proof_explain(args, kwargs):
        """प्रमाण_व्याख्या(इकाई, संबंध, गुण) → शब्दकोश — Explain proof result."""
        if len(args) < 3:
            raise VakRuntimeError("प्रमाण_व्याख्या: इकाई, संबंध, गुण चाहिए")
        return _engine.explain((str(args[0]), str(args[1]), str(args[2])))

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
        "पश्च_सिद्ध_है": _backward_provable,
        "प्रमाण_लॉग":   _proof_log,    # get proof log
        "प्रमाण_सारांश": _proof_summary,
        "प्रमाण_स्नैपशॉट": _proof_snapshot,
        "प्रमाण_पुनर्स्थापय": _proof_restore,
        "प्रमाण_अनुक्रम": _proof_trace,
        "प्रमाण_वृक्ष": _proof_tree,
        "प्रमाण_व्याख्या": _proof_explain,
        "प्रमाण_रीसेट": _reset_engine, # reset engine
    }

    for name, fn in sansmatic_builtins.items():
        globals_env.define(name, BuiltinFunction(name, fn))
