from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class VakType:
    def display(self) -> str:
        return str(self)


@dataclass(frozen=True)
class AnyType(VakType):
    def __str__(self) -> str:
        return "कोईभी"


@dataclass(frozen=True)
class NeverType(VakType):
    def __str__(self) -> str:
        return "never"


@dataclass(frozen=True)
class PrimitiveType(VakType):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ListType(VakType):
    element_type: VakType

    def __str__(self) -> str:
        return f"सूची[{self.element_type}]"


@dataclass(frozen=True)
class SetType(VakType):
    element_type: VakType

    def __str__(self) -> str:
        return f"समुच्चय[{self.element_type}]"


@dataclass(frozen=True)
class DictType(VakType):
    key_type: VakType
    value_type: VakType

    def __str__(self) -> str:
        return f"शब्दकोश[{self.key_type}, {self.value_type}]"


@dataclass(frozen=True)
class TupleType(VakType):
    element_types: tuple[VakType, ...]

    def __str__(self) -> str:
        inner = ", ".join(str(t) for t in self.element_types)
        return f"({inner})"


@dataclass(frozen=True)
class UnionType(VakType):
    options: tuple[VakType, ...]

    def __str__(self) -> str:
        return " | ".join(str(option) for option in self.options)


@dataclass(frozen=True)
class ResultType(VakType):
    ok_type: VakType
    err_type: VakType

    def __str__(self) -> str:
        return f"फल[{self.ok_type}, {self.err_type}]"


@dataclass(frozen=True)
class FunctionType(VakType):
    param_types: tuple[VakType, ...]
    return_type: VakType
    param_names: tuple[str, ...] = ()
    defaults_count: int = 0
    varargs_name: str | None = None
    is_async: bool = False

    def __str__(self) -> str:
        params = ", ".join(str(t) for t in self.param_types)
        return f"कर्म({params}) -> {self.return_type}"

    @property
    def min_args(self) -> int:
        return max(0, len(self.param_types) - self.defaults_count)

    @property
    def max_args(self) -> int | None:
        return None if self.varargs_name else len(self.param_types)


@dataclass(frozen=True)
class ClassType(VakType):
    name: str

    def __str__(self) -> str:
        return f"वर्ग[{self.name}]"


@dataclass(frozen=True)
class InstanceType(VakType):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ModuleType(VakType):
    name: str

    def __str__(self) -> str:
        return f"मॉड्यूल[{self.name}]"


@dataclass(frozen=True)
class TypeVarType(VakType):
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ADTType(VakType):
    name: str
    type_args: tuple[VakType, ...] = ()

    def __str__(self) -> str:
        if not self.type_args:
            return self.name
        return f"{self.name}[{', '.join(str(arg) for arg in self.type_args)}]"


@dataclass(frozen=True)
class VariantValueType(VakType):
    data_name: str
    variant_name: str
    field_types: tuple[VakType, ...] = ()
    type_args: tuple[VakType, ...] = ()

    def __str__(self) -> str:
        if self.field_types:
            return f"{self.variant_name}({', '.join(str(t) for t in self.field_types)})"
        return f"{self.variant_name}()"


ANY = AnyType()
NEVER = NeverType()
NULL = PrimitiveType("शून्य")
BOOL = PrimitiveType("बूल")
INT = PrimitiveType("संख्या")
FLOAT = PrimitiveType("दशमलव")
STR = PrimitiveType("तार")
RANGE = PrimitiveType("परास")
OBJECT = PrimitiveType("वस्तु")

TYPE_NAME_ALIASES = {
    "संख्या": INT,
    "पूर्णांक": INT,
    "int": INT,
    "float": FLOAT,
    "दशमलव": FLOAT,
    "तार": STR,
    "str": STR,
    "string": STR,
    "bool": BOOL,
    "बूल": BOOL,
    "बूलियन": BOOL,
    "शून्य": NULL,
    "none": NULL,
    "null": NULL,
    "सूची": ListType(ANY),
    "list": ListType(ANY),
    "समुच्चय": SetType(ANY),
    "set": SetType(ANY),
    "शब्दकोश": DictType(ANY, ANY),
    "dict": DictType(ANY, ANY),
    "परास": RANGE,
    "range": RANGE,
    "वस्तु": OBJECT,
    "object": OBJECT,
}

ADT_REGISTRY: dict[str, dict[str, object]] = {}


def parse_type_hint(name: str | None) -> VakType:
    if not name:
        return ANY
    text = name.strip()
    if not text:
        return ANY

    union_parts = _split_top_level(text, "|")
    if len(union_parts) > 1:
        return UnionType(tuple(parse_type_hint(part) for part in union_parts))

    if text.startswith("(") and text.endswith(")"):
        inner = text[1:-1].strip()
        if inner:
            tuple_parts = _split_top_level(inner, ",")
            if len(tuple_parts) > 1:
                return TupleType(tuple(parse_type_hint(part) for part in tuple_parts))

    generic = _parse_generic_type(text)
    if generic is not None:
        return generic

    alias = TYPE_NAME_ALIASES.get(text)
    if alias is not None:
        return alias

    if _looks_like_type_var(text):
        return TypeVarType(text)
    if text in ADT_REGISTRY:
        return ADTType(text)
    return InstanceType(text)


def _split_top_level(text: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    depth_square = 0
    depth_round = 0
    start = 0
    for index, char in enumerate(text):
        if char == "[":
            depth_square += 1
        elif char == "]":
            depth_square -= 1
        elif char == "(":
            depth_round += 1
        elif char == ")":
            depth_round -= 1
        elif char == delimiter and depth_square == 0 and depth_round == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def _parse_generic_type(text: str) -> VakType | None:
    if "[" not in text or not text.endswith("]"):
        return None

    base, _, rest = text.partition("[")
    base = base.strip()
    inner = rest[:-1].strip()
    args = _split_top_level(inner, ",") if inner else []
    parsed_args = [parse_type_hint(arg) for arg in args]

    if base in ("सूची", "list"):
        return ListType(parsed_args[0] if parsed_args else ANY)
    if base in ("समुच्चय", "set"):
        return SetType(parsed_args[0] if parsed_args else ANY)
    if base in ("शब्दकोश", "dict"):
        key_type = parsed_args[0] if len(parsed_args) >= 1 else ANY
        value_type = parsed_args[1] if len(parsed_args) >= 2 else ANY
        return DictType(key_type, value_type)
    if base in ("फल", "Result"):
        ok_type = parsed_args[0] if len(parsed_args) >= 1 else ANY
        err_type = parsed_args[1] if len(parsed_args) >= 2 else ANY
        return ResultType(ok_type, err_type)
    if base in ADT_REGISTRY:
        return ADTType(base, tuple(parsed_args))
    return InstanceType(f"{base}[{', '.join(args)}]")


def _looks_like_type_var(text: str) -> bool:
    if not text:
        return False
    if len(text) == 1 and text.isupper():
        return True
    return text in {"T", "E", "K", "V"}


def register_adt_type(name: str, variants: Iterable[str] | None = None, type_params: Iterable[str] | None = None) -> None:
    params = tuple(type_params or ())
    ADT_REGISTRY[name] = {
        "variants": tuple(variants or ()),
        "type_params": params,
    }
    TYPE_NAME_ALIASES[name] = ADTType(name, tuple(TypeVarType(param) for param in params))


def instantiate_type(template: VakType, bindings: dict[str, VakType]) -> VakType:
    if isinstance(template, TypeVarType):
        return bindings.get(template.name, template)
    if isinstance(template, ListType):
        return ListType(instantiate_type(template.element_type, bindings))
    if isinstance(template, SetType):
        return SetType(instantiate_type(template.element_type, bindings))
    if isinstance(template, DictType):
        return DictType(
            instantiate_type(template.key_type, bindings),
            instantiate_type(template.value_type, bindings),
        )
    if isinstance(template, TupleType):
        return TupleType(tuple(instantiate_type(item, bindings) for item in template.element_types))
    if isinstance(template, UnionType):
        return UnionType(tuple(instantiate_type(item, bindings) for item in template.options))
    if isinstance(template, ResultType):
        return ResultType(
            instantiate_type(template.ok_type, bindings),
            instantiate_type(template.err_type, bindings),
        )
    if isinstance(template, ADTType):
        return ADTType(template.name, tuple(instantiate_type(arg, bindings) for arg in template.type_args))
    if isinstance(template, VariantValueType):
        return VariantValueType(
            template.data_name,
            template.variant_name,
            tuple(instantiate_type(item, bindings) for item in template.field_types),
            tuple(instantiate_type(arg, bindings) for arg in template.type_args),
        )
    return template


def bind_typevars(pattern: VakType, actual: VakType, bindings: dict[str, VakType]) -> bool:
    if isinstance(pattern, TypeVarType):
        existing = bindings.get(pattern.name)
        if existing is None:
            bindings[pattern.name] = actual
            return True
        return is_assignable(actual, existing) or is_assignable(existing, actual)
    if isinstance(pattern, ListType) and isinstance(actual, ListType):
        return bind_typevars(pattern.element_type, actual.element_type, bindings)
    if isinstance(pattern, SetType) and isinstance(actual, SetType):
        return bind_typevars(pattern.element_type, actual.element_type, bindings)
    if isinstance(pattern, DictType) and isinstance(actual, DictType):
        return bind_typevars(pattern.key_type, actual.key_type, bindings) and bind_typevars(pattern.value_type, actual.value_type, bindings)
    if isinstance(pattern, TupleType) and isinstance(actual, TupleType) and len(pattern.element_types) == len(actual.element_types):
        return all(bind_typevars(src, dst, bindings) for src, dst in zip(pattern.element_types, actual.element_types))
    if isinstance(pattern, ResultType) and isinstance(actual, ResultType):
        return bind_typevars(pattern.ok_type, actual.ok_type, bindings) and bind_typevars(pattern.err_type, actual.err_type, bindings)
    if isinstance(pattern, ADTType) and isinstance(actual, ADTType) and pattern.name == actual.name and len(pattern.type_args) == len(actual.type_args):
        return all(bind_typevars(src, dst, bindings) for src, dst in zip(pattern.type_args, actual.type_args))
    return is_assignable(actual, pattern)


def _dedupe_types(types: Iterable[VakType]) -> list[VakType]:
    unique: list[VakType] = []
    for item in types:
        if item == NEVER:
            continue
        if item not in unique:
            unique.append(item)
    return unique


def combine_types(*types: VakType) -> VakType:
    flat: list[VakType] = []
    for item in types:
        if isinstance(item, UnionType):
            flat.extend(item.options)
        else:
            flat.append(item)

    unique = _dedupe_types(flat)
    if not unique:
        return NEVER
    if ANY in unique:
        return ANY
    result_types = [item for item in unique if isinstance(item, ResultType)]
    if len(result_types) == len(unique):
        return ResultType(
            combine_types(*(item.ok_type for item in result_types)),
            combine_types(*(item.err_type for item in result_types)),
        )
    list_types = [item for item in unique if isinstance(item, ListType)]
    if len(list_types) == len(unique):
        return ListType(combine_types(*(item.element_type for item in list_types)))
    set_types = [item for item in unique if isinstance(item, SetType)]
    if len(set_types) == len(unique):
        return SetType(combine_types(*(item.element_type for item in set_types)))
    dict_types = [item for item in unique if isinstance(item, DictType)]
    if len(dict_types) == len(unique):
        return DictType(
            combine_types(*(item.key_type for item in dict_types)),
            combine_types(*(item.value_type for item in dict_types)),
        )
    tuple_types = [item for item in unique if isinstance(item, TupleType)]
    if tuple_types and len(tuple_types) == len(unique):
        tuple_len = len(tuple_types[0].element_types)
        if all(len(item.element_types) == tuple_len for item in tuple_types):
            return TupleType(
                tuple(
                    combine_types(*(item.element_types[index] for item in tuple_types))
                    for index in range(tuple_len)
                )
            )
    variant_types = [item for item in unique if isinstance(item, VariantValueType)]
    if variant_types and len(variant_types) == len(unique):
        data_name = variant_types[0].data_name
        if all(item.data_name == data_name for item in variant_types):
            type_arg_count = len(variant_types[0].type_args)
            if all(len(item.type_args) == type_arg_count for item in variant_types):
                return ADTType(
                    data_name,
                    tuple(
                        combine_types(*(item.type_args[index] for item in variant_types))
                        for index in range(type_arg_count)
                    ),
                )
    if len(unique) == 1:
        return unique[0]
    if INT in unique and FLOAT in unique and len(unique) == 2:
        return FLOAT
    return UnionType(tuple(unique))


def is_assignable(value_type: VakType, target_type: VakType) -> bool:
    if target_type == ANY or value_type == ANY:
        return True
    if value_type == NEVER:
        return True
    if isinstance(target_type, TypeVarType):
        return True
    if isinstance(value_type, TypeVarType):
        return True
    if value_type == target_type:
        return True
    if target_type == OBJECT:
        return True
    if value_type == NULL and isinstance(target_type, UnionType):
        return any(is_assignable(value_type, option) for option in target_type.options)
    if isinstance(target_type, UnionType):
        return any(is_assignable(value_type, option) for option in target_type.options)
    if isinstance(value_type, UnionType):
        return all(is_assignable(option, target_type) for option in value_type.options)
    if value_type == INT and target_type == FLOAT:
        return True
    if isinstance(value_type, ListType) and isinstance(target_type, ListType):
        return is_assignable(value_type.element_type, target_type.element_type)
    if isinstance(value_type, SetType) and isinstance(target_type, SetType):
        return is_assignable(value_type.element_type, target_type.element_type)
    if isinstance(value_type, DictType) and isinstance(target_type, DictType):
        return (
            is_assignable(value_type.key_type, target_type.key_type)
            and is_assignable(value_type.value_type, target_type.value_type)
        )
    if isinstance(value_type, TupleType) and isinstance(target_type, TupleType):
        return (
            len(value_type.element_types) == len(target_type.element_types)
            and all(
                is_assignable(src, dst)
                for src, dst in zip(value_type.element_types, target_type.element_types)
            )
        )
    if isinstance(value_type, ResultType) and isinstance(target_type, ResultType):
        return (
            is_assignable(value_type.ok_type, target_type.ok_type)
            and is_assignable(value_type.err_type, target_type.err_type)
        )
    if isinstance(value_type, VariantValueType) and isinstance(target_type, ADTType):
        if value_type.data_name != target_type.name:
            return False
        if not target_type.type_args:
            return True
        if len(value_type.type_args) != len(target_type.type_args):
            return False
        return all(
            is_assignable(src, dst)
            for src, dst in zip(value_type.type_args, target_type.type_args)
        )
    if isinstance(value_type, VariantValueType) and isinstance(target_type, VariantValueType):
        return (
            value_type.data_name == target_type.data_name
            and value_type.variant_name == target_type.variant_name
            and len(value_type.field_types) == len(target_type.field_types)
            and all(
                is_assignable(src, dst)
                for src, dst in zip(value_type.field_types, target_type.field_types)
            )
        )
    if isinstance(value_type, ADTType) and isinstance(target_type, ADTType):
        if value_type.name != target_type.name:
            return False
        if not target_type.type_args:
            return True
        return (
            len(value_type.type_args) == len(target_type.type_args)
            and all(
                is_assignable(src, dst)
                for src, dst in zip(value_type.type_args, target_type.type_args)
            )
        )
    if isinstance(value_type, TypeVarType) and isinstance(target_type, TypeVarType):
        return value_type.name == target_type.name
    if isinstance(value_type, InstanceType) and isinstance(target_type, InstanceType):
        return value_type.name == target_type.name
    if isinstance(value_type, ModuleType) and isinstance(target_type, ModuleType):
        return value_type.name == target_type.name
    return False


def iterable_element_type(value_type: VakType) -> VakType:
    if value_type == ANY:
        return ANY
    if value_type == RANGE:
        return INT
    if value_type == STR:
        return STR
    if isinstance(value_type, ListType):
        return value_type.element_type
    if isinstance(value_type, SetType):
        return value_type.element_type
    if isinstance(value_type, TupleType):
        return combine_types(*value_type.element_types)
    if isinstance(value_type, UnionType):
        return combine_types(*(iterable_element_type(option) for option in value_type.options))
    return ANY
