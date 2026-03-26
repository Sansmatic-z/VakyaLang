# आत्मलिपि सेतु — AtmaLipi Bridge for वाक् Language
# © 2026 Raj Mitra

import sys, os
unified_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if unified_root not in sys.path:
    sys.path.insert(0, unified_root)

from atmalipi.src.engine import AtmaLipiEngine, AtmaValue
from ..errors import VakRuntimeError

_atma = AtmaLipiEngine()


def register_atmalipi_bridge(globals_env):
    """Register AtmaLipi consciousness metadata functions into वाक् scope."""

    from ..interpreter import BuiltinFunction

    def _atma_wrap(args, kwargs):
        """
        आत्म_मूल्य(मूल्य, भाव=None, अवस्था=None, टिप्पणी=None)
        Wrap a value with consciousness metadata.
        Returns an AtmaValue object — prints with {भाव} [अवस्था] format.
        """
        if not args:
            raise VakRuntimeError("आत्म_मूल्य: मूल्य चाहिए")
        value   = args[0]
        bhav    = str(args[1]) if len(args) > 1 else None
        avastha = str(args[2]) if len(args) > 2 else None
        note    = str(args[3]) if len(args) > 3 else None
        return _atma.wrap(value, bhav, avastha, note)

    def _bhav_पढ़ो(args, kwargs):
        """भाव_पढ़ो(tag) — Translate emotional tag."""
        if not args:
            raise VakRuntimeError("भाव_पढ़ो: टैग चाहिए")
        return _atma.read_bhav(str(args[0]))

    def _avastha_पढ़ो(args, kwargs):
        """अवस्था_पढ़ो(tag) — Translate cognitive tag."""
        if not args:
            raise VakRuntimeError("अवस्था_पढ़ो: टैग चाहिए")
        return _atma.read_avastha(str(args[0]))

    def _सभी_भाव(args, kwargs):
        """सभी_भाव() — List all emotional tags."""
        result = []
        for sk, en in _atma.all_bhav().items():
            result.append(f"{sk} → {en}")
        return result

    def _सभी_अवस्था(args, kwargs):
        """सभी_अवस्था() — List all cognitive tags."""
        result = []
        for sk, en in _atma.all_avastha().items():
            result.append(f"{sk} → {en}")
        return result

    def _आत्म_इतिहास(args, kwargs):
        """आत्म_इतिहास() — Full history of wrapped values."""
        return _atma.get_history()

    def _है_आत्म_मूल्य(args, kwargs):
        """आत्म_है(x) → सत्य if x is an AtmaValue."""
        return isinstance(args[0], AtmaValue) if args else False

    def _आत्म_भाव(args, kwargs):
        """आत्म_भाव(x) → भाव tag of an AtmaValue."""
        if args and isinstance(args[0], AtmaValue):
            return args[0].bhav or "शून्य"
        return "शून्य"

    def _आत्म_अवस्था(args, kwargs):
        """आत्म_अवस्था(x) → अवस्था tag of an AtmaValue."""
        if args and isinstance(args[0], AtmaValue):
            return args[0].avastha or "शून्य"
        return "शून्य"

    def _आत्म_मूल(args, kwargs):
        """आत्म_मूल(x) → unwrap to raw value."""
        if args and isinstance(args[0], AtmaValue):
            return args[0].value
        return args[0] if args else None

    atmalipi_builtins = {
        "आत्म_मूल्य":   _atma_wrap,        # wrap value with metadata
        "भाव_पढ़ो":      _bhav_पढ़ो,         # translate emotional tag
        "अवस्था_पढ़ो":   _avastha_पढ़ो,      # translate cognitive tag
        "सभी_भाव":      _सभी_भाव,          # list all emotional tags
        "सभी_अवस्था":   _सभी_अवस्था,       # list all cognitive tags
        "आत्म_इतिहास":  _आत्म_इतिहास,      # full metadata history
        "आत्म_है":       _है_आत्म_मूल्य,    # is AtmaValue?
        "आत्म_भाव":      _आत्म_भाव,         # get भाव of AtmaValue
        "आत्म_अवस्था":   _आत्म_अवस्था,      # get अवस्था of AtmaValue
        "आत्म_मूल":      _आत्म_मूल,         # unwrap to raw value
    }

    for name, fn in atmalipi_builtins.items():
        globals_env.define(name, BuiltinFunction(name, fn))
