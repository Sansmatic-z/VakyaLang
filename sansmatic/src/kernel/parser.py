from __future__ import annotations

from dataclasses import dataclass
import re

from .errors import KernelTypeError
from .syntax import Absurd, Ann, App, EmptyType, EqType, Fst, Inl, Inr, KernelTerm, Lam, NatElim, NatLit, NatSucc, NatType, Pair, Pi, Refl, Sigma, SumElim, SumType, Snd, Sort, Transport, UnitIntro, UnitType, Var


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str


_IDENT_RE = re.compile(r"[^\W\d]\w*", re.UNICODE)
_DIGITS_RE = re.compile(r"\d+")


class KernelParser:
    """
    Small parser for additive Sansmatic kernel terms.

    Supported syntax:
    - `Type`, `Type0`, `Type1`, ...
    - `Nat`, `Unit`, `Empty`, numeric literals
    - `unit`, `absurd T p`
    - `succ n`, `nat_elim P z s n`
    - `Sum A B`, `inl x B`, `inr A y`, `sum_elim P l r s`
    - `transport A P x y p u`
    - `x`
    - `Σ x: A. B` / `Sigma x: A. B`
    - `pair a b`, `fst p`, `snd p`
    - `Eq A x y`
    - `refl x`
    - `(t : T)` explicit annotation
    - `λ x: Nat. x` / `lambda x: Nat. x`
    - `Π x: A. B` / `Pi x: A. B`
    - application: `f x y`
    - arrows: `A -> B` desugared to `Π _: A. B`
    """

    def parse_term(self, source: str) -> KernelTerm:
        self._tokens = self._tokenize(source)
        self._pos = 0
        term = self._term()
        self._expect("EOF")
        return term

    def _tokenize(self, source: str) -> list[_Token]:
        tokens: list[_Token] = []
        index = 0
        while index < len(source):
            char = source[index]
            if char.isspace():
                index += 1
                continue
            if source.startswith("->", index):
                tokens.append(_Token("ARROW", "->"))
                index += 2
                continue
            if char in "():.":
                tokens.append(_Token(char, char))
                index += 1
                continue
            if char == "λ":
                tokens.append(_Token("LAMBDA", char))
                index += 1
                continue
            if char == "Π":
                tokens.append(_Token("PI", char))
                index += 1
                continue
            if char == "Σ":
                tokens.append(_Token("SIGMA", char))
                index += 1
                continue

            number = _DIGITS_RE.match(source, index)
            if number:
                tokens.append(_Token("NAT", number.group(0)))
                index = number.end()
                continue

            ident = _IDENT_RE.match(source, index)
            if ident:
                text = ident.group(0)
                kind = {
                    "lambda": "LAMBDA",
                    "Pi": "PI",
                    "Sigma": "SIGMA",
                    "pair": "PAIR",
                    "inl": "INL",
                    "inr": "INR",
                    "fst": "FST",
                    "snd": "SND",
                    "succ": "SUCC",
                    "nat_elim": "NAT_ELIM",
                    "NatElim": "NAT_ELIM",
                    "sum_elim": "SUM_ELIM",
                    "SumElim": "SUM_ELIM",
                    "absurd": "ABSURD",
                    "transport": "TRANSPORT",
                    "Sum": "SUM",
                    "Eq": "EQ",
                    "refl": "REFL",
                }.get(text, "IDENT")
                tokens.append(_Token(kind, text))
                index = ident.end()
                continue

            raise KernelTypeError(f"Unexpected kernel token near: {source[index:index + 20]!r}")

        tokens.append(_Token("EOF", ""))
        return tokens

    def _current(self) -> _Token:
        return self._tokens[self._pos]

    def _advance(self) -> _Token:
        token = self._current()
        self._pos += 1
        return token

    def _match(self, *kinds: str) -> _Token | None:
        if self._current().kind in kinds:
            return self._advance()
        return None

    def _expect(self, kind: str) -> _Token:
        token = self._match(kind)
        if token is None:
            current = self._current()
            raise KernelTypeError(f"Expected {kind}, got {current.kind} ({current.value!r})")
        return token

    def _term(self) -> KernelTerm:
        return self._lambda_or_pi()

    def _lambda_or_pi(self) -> KernelTerm:
        if self._match("LAMBDA"):
            name = self._expect("IDENT").value
            self._expect(":")
            param_type = self._term()
            self._expect(".")
            body = self._term()
            return Lam(name, param_type, body)
        if self._match("PI"):
            name = self._expect("IDENT").value
            self._expect(":")
            param_type = self._term()
            self._expect(".")
            body = self._term()
            return Pi(name, param_type, body)
        if self._match("SIGMA"):
            name = self._expect("IDENT").value
            self._expect(":")
            param_type = self._term()
            self._expect(".")
            body = self._term()
            return Sigma(name, param_type, body)
        return self._arrow()

    def _arrow(self) -> KernelTerm:
        left = self._application()
        if self._match("ARROW"):
            right = self._arrow()
            return Pi("_", left, right)
        return left

    def _application(self) -> KernelTerm:
        term = self._atom()
        while self._current().kind in {"IDENT", "NAT", "(", "PAIR", "INL", "INR", "FST", "SND", "SUCC", "NAT_ELIM", "SUM_ELIM", "ABSURD", "TRANSPORT", "SUM", "EQ", "REFL"}:
            term = App(term, self._atom())
        return term

    def _atom(self) -> KernelTerm:
        current = self._current()
        if self._match("("):
            inner = self._term()
            if self._match(":"):
                annotation = self._term()
                self._expect(")")
                return Ann(inner, annotation)
            self._expect(")")
            return inner
        if token := self._match("NAT"):
            return NatLit(int(token.value))
        if self._match("PAIR"):
            return Pair(
                self._atom(),
                self._atom(),
            )
        if self._match("INL"):
            return Inl(
                self._atom(),
                self._atom(),
            )
        if self._match("INR"):
            return Inr(
                self._atom(),
                self._atom(),
            )
        if self._match("FST"):
            return Fst(self._atom())
        if self._match("SND"):
            return Snd(self._atom())
        if self._match("SUCC"):
            return NatSucc(self._atom())
        if self._match("NAT_ELIM"):
            return NatElim(
                self._atom(),
                self._atom(),
                self._atom(),
                self._atom(),
            )
        if self._match("SUM_ELIM"):
            return SumElim(
                self._atom(),
                self._atom(),
                self._atom(),
                self._atom(),
            )
        if self._match("ABSURD"):
            return Absurd(
                self._atom(),
                self._atom(),
            )
        if self._match("TRANSPORT"):
            return Transport(
                self._atom(),
                self._atom(),
                self._atom(),
                self._atom(),
                self._atom(),
                self._atom(),
            )
        if self._match("SUM"):
            return SumType(
                self._atom(),
                self._atom(),
            )
        if self._match("EQ"):
            return EqType(
                self._atom(),
                self._atom(),
                self._atom(),
            )
        if self._match("REFL"):
            return Refl(self._atom())
        if token := self._match("IDENT"):
            if token.value == "Nat":
                return NatType()
            if token.value == "Unit":
                return UnitType()
            if token.value == "unit":
                return UnitIntro()
            if token.value == "Empty":
                return EmptyType()
            if token.value.startswith("Type"):
                suffix = token.value[4:]
                if suffix == "":
                    return Sort(0)
                if suffix.isdigit():
                    return Sort(int(suffix))
            return Var(token.value)
        raise KernelTypeError(f"Unexpected kernel atom: {current.kind} ({current.value!r})")
