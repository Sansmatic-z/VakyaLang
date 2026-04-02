from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _normalize_items(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _canonical_text(value: Any) -> str:
    return str(value).strip().lower()


ESSENCE_ALIASES = {
    "संख्या": "संख्या",
    "number": "संख्या",
    "numeric": "संख्या",
    "तार": "तार",
    "string": "तार",
    "text": "तार",
    "सूची": "सूची",
    "list": "सूची",
    "collection": "सूची",
    "शब्दकोश": "शब्दकोश",
    "dict": "शब्दकोश",
    "mapping": "शब्दकोश",
    "तर्क": "तर्क",
    "bool": "तर्क",
    "boolean": "तर्क",
    "रिक्त": "रिक्त",
    "null": "रिक्त",
    "none": "रिक्त",
    "वस्तु": "वस्तु",
    "object": "वस्तु",
}

PROPERTY_ALIASES = {
    "धनात्मक": "धनात्मक",
    "positive": "धनात्मक",
    "अधनात्मक": "अधनात्मक",
    "nonnegative": "अधनात्मक",
    "non_negative": "अधनात्मक",
    "ऋणात्मक": "ऋणात्मक",
    "negative": "ऋणात्मक",
    "रिक्त_नहीं": "रिक्त_नहीं",
    "nonempty": "रिक्त_नहीं",
    "non_empty": "रिक्त_नहीं",
    "सम": "सम",
    "even": "सम",
    "विषम": "विषम",
    "odd": "विषम",
    "सत्य": "सत्य",
    "truthy": "सत्य",
}

ROLE_ALIASES = {
    "कर्ता": "कर्ता",
    "karta": "कर्ता",
    "agent": "कर्ता",
    "कर्म": "कर्म",
    "karma": "कर्म",
    "object": "कर्म",
    "करण": "करण",
    "karana": "करण",
    "instrument": "करण",
    "अधिकरण": "अधिकरण",
    "adhikarana": "अधिकरण",
    "location": "अधिकरण",
    "सम्प्रदान": "सम्प्रदान",
    "sampradana": "सम्प्रदान",
    "recipient": "सम्प्रदान",
    "अपादान": "अपादान",
    "apadana": "अपादान",
    "source": "अपादान",
    "सम्बन्ध": "सम्बन्ध",
    "sambandha": "सम्बन्ध",
    "relation": "सम्बन्ध",
}


def classify_padartha(value: Any) -> str:
    if value is None:
        return "अभाव"
    if callable(value):
        return "कर्म"
    if isinstance(value, bool):
        return "गुण"
    if isinstance(value, (int, float, str, list, tuple, dict, set)):
        return "द्रव्य"
    return "द्रव्य"


def _essence_matches(essence: str, value: Any) -> bool:
    if essence == "संख्या":
        return _is_number(value)
    if essence == "तार":
        return isinstance(value, str)
    if essence == "सूची":
        return isinstance(value, (list, tuple, set))
    if essence == "शब्दकोश":
        return isinstance(value, dict)
    if essence == "तर्क":
        return isinstance(value, bool)
    if essence == "रिक्त":
        return value is None
    if essence == "वस्तु":
        return True
    return True


def _property_matches(prop: str, value: Any) -> bool:
    if prop == "धनात्मक":
        return _is_number(value) and value > 0
    if prop == "अधनात्मक":
        return _is_number(value) and value >= 0
    if prop == "ऋणात्मक":
        return _is_number(value) and value < 0
    if prop == "रिक्त_नहीं":
        return hasattr(value, "__len__") and len(value) > 0
    if prop == "सम":
        return isinstance(value, int) and not isinstance(value, bool) and value % 2 == 0
    if prop == "विषम":
        return isinstance(value, int) and not isinstance(value, bool) and value % 2 == 1
    if prop == "सत्य":
        return bool(value)
    return True


def _normalize_alias(value: Any, aliases: dict[str, str], kind: str) -> str:
    if value is None:
        raise ValueError(f"{kind} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{kind} is required")
    return aliases.get(text.lower(), text)


def _normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"सत्य", "true", "yes", "1"}:
        return True
    if text in {"असत्य", "false", "no", "0"}:
        return False
    return default


@dataclass(frozen=True)
class DharmaSpec:
    name: str
    essence: str
    properties: tuple[str, ...] = field(default_factory=tuple)
    operations: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""

    @classmethod
    def from_value(cls, value: Any) -> "DharmaSpec":
        if isinstance(value, DharmaSpec):
            return value
        if not isinstance(value, dict):
            raise ValueError("dharma specification must be a dictionary")
        return cls(
            name=str(value.get("नाम") or value.get("name") or "").strip(),
            essence=_normalize_alias(
                value.get("सार") or value.get("essence"),
                ESSENCE_ALIASES,
                "dharma essence",
            ),
            properties=tuple(
                _normalize_alias(item, PROPERTY_ALIASES, "dharma property")
                for item in _normalize_items(value.get("गुण") or value.get("properties"))
            ),
            operations=tuple(str(item) for item in _normalize_items(value.get("क्रिया") or value.get("operations"))),
            description=str(value.get("विवरण") or value.get("description") or ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "नाम": self.name,
            "name": self.name,
            "सार": self.essence,
            "essence": self.essence,
            "गुण": list(self.properties),
            "properties": list(self.properties),
            "क्रिया": list(self.operations),
            "operations": list(self.operations),
            "विवरण": self.description,
            "description": self.description,
        }


@dataclass(frozen=True)
class KarakaParamSpec:
    name: str
    role: str
    required: bool = True
    default: Any = None

    @classmethod
    def from_value(cls, value: Any) -> "KarakaParamSpec":
        if isinstance(value, KarakaParamSpec):
            return value
        if isinstance(value, dict):
            return cls(
                name=str(value.get("नाम") or value.get("name") or "").strip(),
                role=_normalize_alias(
                    value.get("भूमिका") or value.get("role"),
                    ROLE_ALIASES,
                    "karaka role",
                ),
                required=_normalize_bool(value.get("आवश्यक") if "आवश्यक" in value else value.get("required"), True),
                default=value.get("मूल") if "मूल" in value else value.get("default"),
            )
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return cls(
                name=str(value[0]).strip(),
                role=_normalize_alias(value[1], ROLE_ALIASES, "karaka role"),
                required=_normalize_bool(value[2], True) if len(value) > 2 else True,
                default=value[3] if len(value) > 3 else None,
            )
        raise ValueError("karaka parameter must be a dict or tuple")

    def to_dict(self) -> dict[str, Any]:
        return {
            "नाम": self.name,
            "name": self.name,
            "भूमिका": self.role,
            "role": self.role,
            "आवश्यक": self.required,
            "required": self.required,
            "मूल": self.default,
            "default": self.default,
        }


@dataclass(frozen=True)
class KarakaSignatureSpec:
    verb: str
    params: tuple[KarakaParamSpec, ...] = field(default_factory=tuple)

    @classmethod
    def from_value(cls, value: Any) -> "KarakaSignatureSpec":
        if isinstance(value, KarakaSignatureSpec):
            return value
        if not isinstance(value, dict):
            raise ValueError("karaka signature must be a dictionary")
        params = tuple(
            KarakaParamSpec.from_value(item)
            for item in _normalize_items(value.get("पैरामीटर") or value.get("params"))
        )
        return cls(
            verb=str(value.get("क्रिया") or value.get("verb") or "").strip(),
            params=params,
        )

    def to_dict(self) -> dict[str, Any]:
        required_roles = [param.role for param in self.params if param.required]
        optional_roles = [param.role for param in self.params if not param.required]
        return {
            "क्रिया": self.verb,
            "verb": self.verb,
            "पैरामीटर": [param.to_dict() for param in self.params],
            "params": [param.to_dict() for param in self.params],
            "आवश्यक_भूमिकाएँ": required_roles,
            "required_roles": required_roles,
            "वैकल्पिक_भूमिकाएँ": optional_roles,
            "optional_roles": optional_roles,
        }


def create_dharma_spec(
    name: Any,
    essence: Any,
    properties: Any = None,
    operations: Any = None,
    description: Any = "",
) -> dict[str, Any]:
    spec = DharmaSpec(
        name=str(name).strip(),
        essence=_normalize_alias(essence, ESSENCE_ALIASES, "dharma essence"),
        properties=tuple(
            _normalize_alias(item, PROPERTY_ALIASES, "dharma property")
            for item in _normalize_items(properties)
        ),
        operations=tuple(str(item) for item in _normalize_items(operations)),
        description=str(description or ""),
    )
    if not spec.name:
        raise ValueError("dharma name is required")
    return spec.to_dict()


def validate_dharma_value(spec_value: Any, value: Any) -> dict[str, Any]:
    spec = DharmaSpec.from_value(spec_value)
    if not spec.name:
        raise ValueError("dharma name is required")
    if not _essence_matches(spec.essence, value):
        message = f"Value does not satisfy dharma essence '{spec.essence}'"
        return {
            "मान्य": False,
            "valid": False,
            "संदेश": message,
            "message": message,
            "धर्म": spec.name,
            "dharma": spec.name,
            "सार": spec.essence,
            "essence": spec.essence,
            "विफल_गुण": None,
            "failed_property": None,
            "पदार्थ": classify_padartha(value),
            "padartha": classify_padartha(value),
        }

    for prop in spec.properties:
        if not _property_matches(prop, value):
            message = f"Value does not satisfy dharma property '{prop}'"
            return {
                "मान्य": False,
                "valid": False,
                "संदेश": message,
                "message": message,
                "धर्म": spec.name,
                "dharma": spec.name,
                "सार": spec.essence,
                "essence": spec.essence,
                "विफल_गुण": prop,
                "failed_property": prop,
                "पदार्थ": classify_padartha(value),
                "padartha": classify_padartha(value),
            }

    message = f"Value preserves dharma '{spec.name}'"
    return {
        "मान्य": True,
        "valid": True,
        "संदेश": message,
        "message": message,
        "धर्म": spec.name,
        "dharma": spec.name,
        "सार": spec.essence,
        "essence": spec.essence,
        "विफल_गुण": None,
        "failed_property": None,
        "पदार्थ": classify_padartha(value),
        "padartha": classify_padartha(value),
    }


def build_karaka_signature(verb: Any, params: Any) -> dict[str, Any]:
    signature = KarakaSignatureSpec(
        verb=str(verb).strip(),
        params=tuple(KarakaParamSpec.from_value(item) for item in _normalize_items(params)),
    )
    if not signature.verb:
        raise ValueError("karaka verb is required")
    if not signature.params:
        raise ValueError("karaka signature must declare at least one parameter")
    if any(not param.name for param in signature.params):
        raise ValueError("karaka parameter name is required")
    return signature.to_dict()


def validate_karaka_roles(signature_value: Any, provided_roles: Any) -> dict[str, Any]:
    signature = KarakaSignatureSpec.from_value(signature_value)
    if not isinstance(provided_roles, dict):
        raise ValueError("provided roles must be a dictionary")

    param_names = {param.name for param in signature.params}
    missing_roles = [param.role for param in signature.params if param.required and param.name not in provided_roles]
    unexpected_roles = [name for name in provided_roles if name not in param_names]
    invalid_defaults = [
        param.role
        for param in signature.params
        if param.required and param.name in provided_roles and provided_roles[param.name] is None
    ]

    if missing_roles:
        message = f"Missing required karaka roles: {', '.join(missing_roles)}"
        valid = False
    elif unexpected_roles:
        message = f"Unexpected karaka parameters: {', '.join(unexpected_roles)}"
        valid = False
    elif invalid_defaults:
        message = f"Karaka roles cannot be empty: {', '.join(invalid_defaults)}"
        valid = False
    else:
        message = f"Karaka signature '{signature.verb}' validated"
        valid = True

    required_roles = [param.role for param in signature.params if param.required]
    optional_roles = [param.role for param in signature.params if not param.required]
    return {
        "मान्य": valid,
        "valid": valid,
        "संदेश": message,
        "message": message,
        "क्रिया": signature.verb,
        "verb": signature.verb,
        "अनुपस्थित_भूमिकाएँ": missing_roles,
        "missing_roles": missing_roles,
        "अप्रत्याशित_पैरामीटर": unexpected_roles,
        "unexpected_roles": unexpected_roles,
        "आवश्यक_भूमिकाएँ": required_roles,
        "required_roles": required_roles,
        "वैकल्पिक_भूमिकाएँ": optional_roles,
        "optional_roles": optional_roles,
    }


def validate_nyaya_syllogism(
    pratijna: Any,
    hetu: Any,
    udaharana: Any,
    upanaya: Any,
    nigamana: Any,
) -> dict[str, Any]:
    values = {
        "प्रतिज्ञा": str(pratijna or "").strip(),
        "हेतु": str(hetu or "").strip(),
        "उदाहरण": str(udaharana or "").strip(),
        "उपनय": str(upanaya or "").strip(),
        "निगमन": str(nigamana or "").strip(),
    }
    missing = [name for name, value in values.items() if not value]
    warnings: list[str] = []
    valid = True
    message = "Nyaya syllogism is valid"

    if missing:
        valid = False
        message = f"Nyaya syllogism missing members: {', '.join(missing)}"
    elif _canonical_text(values["प्रतिज्ञा"]) != _canonical_text(values["निगमन"]):
        valid = False
        message = "Conclusion (निगमन) must match thesis (प्रतिज्ञा)"
    else:
        lowered_hetu = _canonical_text(values["हेतु"])
        if " not " in f" {lowered_hetu} " or lowered_hetu.startswith("not ") or lowered_hetu.startswith("no "):
            warnings.append("Hetu contains negation and should be reviewed carefully")

    return {
        "मान्य": valid,
        "valid": valid,
        "संदेश": message,
        "message": message,
        "चेतावनी": warnings,
        "warnings": warnings,
        **values,
    }
