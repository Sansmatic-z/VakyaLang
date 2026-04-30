from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from runtime.src.codex import build_default_codex
from runtime.src.compiler import Compiler
from runtime.src.errors import CompileError, LexerError, ParseError
from runtime.src.interpreter import VakInterpreter
from runtime.src.lexer import Lexer
from runtime.src.parser import Parser
from runtime.src.rupantar import VakyaRupantar
from runtime.src.runtime_catalog import build_builtin_catalog
from runtime.src.stdlib_manifest import build_stdlib_manifest
from runtime.src.tokens import KEYWORDS
from runtime.src.ast_nodes import ClassDecl, ConstDecl, DataDecl, FuncDecl, Program, VarDecl


KEYWORD_DOCS: dict[str, str] = {
    "चर": "चर/मान: variable declaration.",
    "स्थिर": "स्थिर: constant declaration.",
    "कर्म": "कर्म: function declaration.",
    "वर्ग": "वर्ग: class declaration.",
    "यदि": "यदि: conditional branch.",
    "अन्यत्": "अन्यत्: else-if branch.",
    "अन्यथा": "अन्यथा: fallback branch.",
    "यावत्": "यावत्: while loop.",
    "प्रत्येक": "प्रत्येक/प्रति: for-each loop.",
    "आयात": "आयात: import a Vak module.",
    "प्रयत्न": "प्रयत्न/प्रयास: begin a try block.",
    "दोष": "दोष/पकड़ो: catch an exception.",
    "अन्ततः": "अन्ततः: finally block.",
    "उत्क्षिप": "उत्क्षिप: throw an exception value.",
    "अतुल्यकालिक": "अतुल्यकालिक: async function declaration.",
    "प्रतीक्षा": "प्रतीक्षा: await a coroutine or async result.",
    "प्रत्यभिज्ञा": "प्रत्यभिज्ञा: pattern matching.",
    "सूत्र": "सूत्र: Paninian macro rule.",
    "पारिणाम": "पारिणाम: compile-time rewrite/fixpoint declaration.",
    "सिद्धि": "सिद्धि: proof declaration verified through Sansmatic.",
}


BUILTIN_DOCS: dict[str, str] = {
    "मुद्रय": "Builtin print/output function.",
    "पठन": "Read a UTF-8 file from disk.",
    "लेखन": "Write UTF-8 text to disk.",
    "खोलो": "Open a file/context object.",
    "दीर्घता": "Return the length of a sequence or mapping.",
    "परास": "Create a numeric range.",
    "संख्या": "Convert a value to integer form.",
    "दशमलव": "Convert a value to floating-point form.",
    "bool": "Convert a value to Vak truthiness.",
    "list": "Build a list from an iterable.",
    "dict": "Build a dict from key/value tuples.",
    "set": "Build a set-like collection from an iterable.",
    "callable": "Return whether a value can be invoked.",
    "isinstance": "Runtime type/class membership test.",
    "hasattr": "Runtime attribute existence test.",
    "async_sleep": "Suspend the current async flow for a duration.",
    "सेट_टाइमआउट": "Schedule a callback after a delay.",
    "सेट_इंटरवल": "Schedule a repeating callback.",
    "जेसन_पढ़ो": "Parse JSON text into Vak values.",
    "जेसन_लिखो": "Serialize Vak values to JSON text.",
    "परिभाषय": "Register a Sansmatic concept or fact base.",
    "दावा": "Assert a Sansmatic fact/claim.",
    "नियम": "Register a Sansmatic inference rule.",
    "मूल्यांकन": "Evaluate a Sansmatic proof/query.",
}


SYMBOL_KIND = {
    FuncDecl: 12,   # Function
    ClassDecl: 5,   # Class
    ConstDecl: 14,  # Constant
    VarDecl: 13,    # Variable
    DataDecl: 5,    # Treat डेटा like class/category
}


@dataclass
class VakDiagnostic:
    line: int
    message: str
    severity: int = 1
    source: str = "vak"
    character: int = 0
    end_character: int = 200
    code: str | None = None
    data: dict[str, Any] | None = None

    def to_lsp(self) -> dict[str, Any]:
        zero_line = max(self.line - 1, 0)
        payload = {
            "range": {
                "start": {"line": zero_line, "character": self.character},
                "end": {"line": zero_line, "character": self.end_character},
            },
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
        }
        if self.code is not None:
            payload["code"] = self.code
        if self.data is not None:
            payload["data"] = self.data
        return payload


class VakLanguageTools:
    def __init__(self) -> None:
        self.interpreter = VakInterpreter()
        self.keyword_docs = dict(KEYWORD_DOCS)
        self.builtin_catalog = build_builtin_catalog(self.interpreter.vm.builtins)
        self.builtin_docs = dict(BUILTIN_DOCS)
        for name, spec in self.builtin_catalog.items():
            signature = self._builtin_signature_label(name)
            description = spec.description or "Vak builtin available at runtime."
            category = f"category: {spec.category}"
            self.builtin_docs[name] = f"{description}\n\n`{signature}`\n\n{category}"
        self._builtins = sorted(self.interpreter.vm.builtins.keys())
        self._keyword_names = sorted(KEYWORDS.keys())
        self._stdlib_modules = sorted(build_stdlib_manifest().keys())
        self._codex_pages = [item["name"] for item in build_default_codex().list_pages()]

    def analyze_document(self, source: str, filename: str = "<memory>") -> list[VakDiagnostic]:
        diagnostics: list[VakDiagnostic] = []
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            compiler = Compiler(source_path=filename)
            compiler.compile(ast)
        except (LexerError, ParseError, CompileError) as error:
            parse_items = getattr(error, "errors", None) or [error]
            for item in parse_items:
                diagnostics.append(
                    VakDiagnostic(
                        getattr(item, "line", 0) or 1,
                        f"{filename}: {item}",
                        code=type(item).__name__,
                    )
                )
        except Exception as error:
            diagnostics.append(VakDiagnostic(1, f"Internal tooling error: {error}", source="vak-tooling"))

        if self._should_probe_repairs(source, diagnostics):
            rupantar = VakyaRupantar()
            result = rupantar.transform_source(source, source_path=filename)
            if result.source != source:
                diagnostics.append(
                    VakDiagnostic(
                        1,
                        "वाक्य-रूपान्तर इस दस्तावेज़ के लिए सुरक्षित संशोधन सुझाता है",
                        severity=3,
                        source="vak-rupantar",
                        code="rupantar.available",
                    )
                )
            for suggestion in result.suggestions[:8]:
                diagnostics.append(
                    VakDiagnostic(
                        suggestion.line,
                        suggestion.message,
                        severity=3,
                        source="vak-rupantar",
                        code=f"rupantar.{suggestion.confidence}",
                    )
                )
        return diagnostics

    def completion_items(self, source: str, line: int, character: int) -> list[dict[str, Any]]:
        prefix = self._identifier_prefix(source, line, character)
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        for item in self._document_completion_items(source):
            name = item["label"]
            if prefix and not name.startswith(prefix):
                continue
            if name in seen:
                continue
            seen.add(name)
            items.append(item)
        for name in self._keyword_names + self._builtins + self._stdlib_modules + self._codex_pages:
            if prefix and not name.startswith(prefix):
                continue
            if name in seen:
                continue
            seen.add(name)
            if name in self._keyword_names:
                kind = 14
                detail = "keyword"
            elif name in self._builtins:
                kind = 3
                detail = "builtin"
            elif name in self._stdlib_modules:
                kind = 9
                detail = "module"
            else:
                kind = 9
                detail = "codex page"
            items.append(
                {
                    "label": name,
                    "kind": kind,
                    "detail": detail,
                    "documentation": self._describe_name(name),
                }
            )
        return items[:100]

    def hover(self, source: str, line: int, character: int) -> dict[str, Any] | None:
        word = self._word_at(source, line, character)
        if not word:
            return None
        description = self._describe_symbol(source, word) or self._describe_name(word)
        if description is None:
            return None
        return {
            "contents": {
                "kind": "markdown",
                "value": f"**{word}**\n\n{description}",
            }
        }

    def document_symbols(self, source: str) -> list[dict[str, Any]]:
        ast = self._parse_program_for_intellisense(source)
        if ast is None:
            return []
        symbols: list[dict[str, Any]] = []
        for node in ast.body:
            symbol_entries = self._symbol_entries(node)
            symbols.extend(symbol_entries)
        return symbols

    def definition(self, source: str, line: int, character: int, uri: str = "file:///memory") -> list[dict[str, Any]]:
        word = self._word_at(source, line, character)
        if not word:
            return []
        ast = self._parse_program_for_intellisense(source)
        if ast is None:
            return []
        for node in ast.body:
            for symbol in self._symbol_entries(node):
                if symbol["name"] == word:
                    symbol_line = symbol["selectionRange"]["start"]["line"]
                    return [
                        {
                            "uri": uri,
                            "range": {
                                "start": {"line": symbol_line, "character": 0},
                                "end": {"line": symbol_line, "character": len(word)},
                            },
                        }
                    ]
        return []

    def code_actions(
        self,
        source: str,
        *,
        filename: str,
        uri: str,
    ) -> list[dict[str, Any]]:
        actions: list[dict[str, Any]] = []
        rupantar = VakyaRupantar()
        repair_result = rupantar.transform_source(source, source_path=filename)
        if repair_result.source != source:
            actions.append(
                self._full_document_action(
                    uri,
                    source,
                    repair_result.source,
                    title="वाक्य-रूपान्तर: सुरक्षित संशोधन लागू करें",
                    kind="quickfix",
                    diagnostics=[item.to_lsp() for item in self.analyze_document(source, filename)],
                )
            )
        codex = build_default_codex()
        codex_result = codex.transform_source(source, filename=filename, page="auto")
        if (
            codex_result.source != source
            and codex_result.confidence != "do_not_touch"
            and codex_result.source != repair_result.source
        ):
            actions.append(
                self._full_document_action(
                    uri,
                    source,
                    codex_result.source,
                    title=f"कोडेक्स ({codex_result.page}): दस्तावेज़ रूपान्तरित करें",
                    kind="refactor.rewrite",
                )
            )
        return actions[:4]

    def signature_help(self, source: str, line: int, character: int) -> dict[str, Any] | None:
        target, active_parameter = self._call_target_at(source, line, character)
        if not target:
            return None
        signature = self._signature_for_name(source, target)
        if signature is None:
            return None
        return {
            "signatures": [signature],
            "activeSignature": 0,
            "activeParameter": min(active_parameter, max(len(signature.get("parameters", [])) - 1, 0)),
        }

    def _parse_program(self, source: str) -> Program | None:
        try:
            return Parser(Lexer(source).tokenize()).parse()
        except Exception:
            return None

    def _parse_program_for_intellisense(self, source: str) -> Program | None:
        ast = self._parse_program(source)
        if ast is not None:
            return ast
        lines = source.splitlines()
        while lines:
            lines = lines[:-1]
            ast = self._parse_program("\n".join(lines))
            if ast is not None:
                return ast
        return None

    def _describe_name(self, name: str) -> str | None:
        if name in self.keyword_docs:
            return self.keyword_docs[name]
        if name in self.builtin_docs:
            return self.builtin_docs[name]
        if name in self._stdlib_modules:
            return "Vak stdlib module."
        if name in self._codex_pages:
            return "Sanskrit Vakya Universal Codex page."
        if name in self._builtins:
            return "Vak builtin available at runtime."
        return None

    def _describe_symbol(self, source: str, name: str) -> str | None:
        ast = self._parse_program_for_intellisense(source)
        if ast is None:
            return None
        for node in ast.body:
            if isinstance(node, VarDecl) and name in node.names:
                hint = f": {node.type_hint}" if node.type_hint else ""
                return f"`चर {name}{hint}`\n\nTop-level variable declaration."
            if isinstance(node, ConstDecl) and node.name == name:
                hint = f": {node.type_hint}" if node.type_hint else ""
                return f"`स्थिर {name}{hint}`\n\nTop-level constant declaration."
            if isinstance(node, FuncDecl) and node.name == name:
                return f"`{self._func_signature(node)}`\n\nTop-level function declaration."
            if isinstance(node, ClassDecl) and node.name == name:
                return f"`वर्ग {name}`\n\nTop-level class declaration."
            if isinstance(node, DataDecl) and node.name == name:
                params = f"[{', '.join(node.type_params)}]" if node.type_params else ""
                return f"`डेटा {name}{params}`\n\nTop-level data declaration."
        return None

    def _symbol_entries(self, node: Any) -> list[dict[str, Any]]:
        if isinstance(node, VarDecl):
            return [self._make_symbol(name, node, SYMBOL_KIND[VarDecl]) for name in node.names]
        if isinstance(node, ConstDecl):
            return [self._make_symbol(node.name, node, SYMBOL_KIND[ConstDecl])]
        if isinstance(node, FuncDecl):
            return [self._make_symbol(node.name, node, SYMBOL_KIND[FuncDecl])]
        if isinstance(node, ClassDecl):
            return [self._make_symbol(node.name, node, SYMBOL_KIND[ClassDecl])]
        if isinstance(node, DataDecl):
            return [self._make_symbol(node.name, node, SYMBOL_KIND[DataDecl])]
        return []

    def _make_symbol(self, name: str, node: Any, kind: int) -> dict[str, Any]:
        zero_line = max(getattr(node, "line", 1) - 1, 0)
        return {
            "name": name,
            "kind": kind,
            "range": {
                "start": {"line": zero_line, "character": 0},
                "end": {"line": zero_line, "character": max(len(name), 1)},
            },
            "selectionRange": {
                "start": {"line": zero_line, "character": 0},
                "end": {"line": zero_line, "character": max(len(name), 1)},
            },
        }

    def _identifier_prefix(self, source: str, line: int, character: int) -> str:
        lines = source.splitlines()
        if line >= len(lines):
            return ""
        text = lines[line][:character]
        idx = len(text)
        while idx > 0 and (text[idx - 1].isalnum() or text[idx - 1] == "_" or ord(text[idx - 1]) > 127):
            idx -= 1
        return text[idx:]

    def _word_at(self, source: str, line: int, character: int) -> str:
        lines = source.splitlines()
        if line >= len(lines):
            return ""
        text = lines[line]
        if not text:
            return ""
        position = min(character, max(len(text) - 1, 0))
        if position < len(text) and not (text[position].isalnum() or text[position] == "_" or ord(text[position]) > 127):
            if position > 0:
                position -= 1
        if position < 0 or not (text[position].isalnum() or text[position] == "_" or ord(text[position]) > 127):
            return ""

        start = position
        end = position + 1
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_" or ord(text[start - 1]) > 127):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] == "_" or ord(text[end]) > 127):
            end += 1
        return text[start:end]

    def _builtin_signature_label(self, name: str) -> str:
        spec = self.builtin_catalog.get(name)
        if spec is None:
            return f"{name}(...)"
        if spec.accepts_varargs:
            params = "*args"
        else:
            if spec.max_args is None:
                limit = max(spec.required_args, 1)
            else:
                limit = max(spec.max_args, spec.required_args)
            params = ", ".join(f"arg{i + 1}" for i in range(limit))
        if spec.keyword_names:
            kw = ", ".join(f"{name}=..." for name in spec.keyword_names)
            params = f"{params}, {kw}" if params else kw
        return f"{name}({params})"

    def _document_completion_items(self, source: str) -> list[dict[str, Any]]:
        ast = self._parse_program_for_intellisense(source)
        if ast is None:
            return []
        items: list[dict[str, Any]] = []
        for node in ast.body:
            documentation = None
            if isinstance(node, FuncDecl):
                documentation = self._func_signature(node)
            elif isinstance(node, VarDecl):
                documentation = f"चर {', '.join(node.names)}"
            elif isinstance(node, ConstDecl):
                documentation = f"स्थिर {node.name}"
            elif isinstance(node, ClassDecl):
                documentation = f"वर्ग {node.name}"
            elif isinstance(node, DataDecl):
                documentation = f"डेटा {node.name}"
            for symbol in self._symbol_entries(node):
                items.append(
                    {
                        "label": symbol["name"],
                        "kind": symbol["kind"],
                        "detail": "document symbol",
                        "documentation": documentation,
                    }
                )
        return items

    def _func_signature(self, node: FuncDecl) -> str:
        params: list[str] = []
        defaults = list(node.defaults or [])
        for index, param in enumerate(node.params):
            if isinstance(param, tuple):
                name, type_hint = param[0], param[1] if len(param) > 1 else None
            else:
                name = getattr(param, "name", str(param))
                type_hint = getattr(param, "type_hint", None)
            label = name
            if type_hint:
                label += f": {type_hint}"
            if index < len(defaults) and defaults[index] is not None:
                label += " = ..."
            params.append(label)
        if node.varargs:
            params.append(f"*{node.varargs}")
        prefix = "अतुल्यकालिक कर्म" if node.is_async else "कर्म"
        suffix = f" → {node.return_type}" if node.return_type else ""
        return f"{prefix} {node.name}({', '.join(params)}){suffix}"

    def _signature_for_name(self, source: str, name: str) -> dict[str, Any] | None:
        ast = self._parse_program_for_intellisense(source)
        if ast is not None:
            for node in ast.body:
                if isinstance(node, FuncDecl) and node.name == name:
                    parameter_labels = []
                    for index, param in enumerate(node.params):
                        if isinstance(param, tuple):
                            pname, type_hint = param[0], param[1] if len(param) > 1 else None
                        else:
                            pname = getattr(param, "name", str(param))
                            type_hint = getattr(param, "type_hint", None)
                        label = pname
                        if type_hint:
                            label += f": {type_hint}"
                        if index < len(node.defaults or []) and node.defaults[index] is not None:
                            label += " = ..."
                        parameter_labels.append({"label": label})
                    return {
                        "label": self._func_signature(node),
                        "documentation": "User-defined Vak function.",
                        "parameters": parameter_labels,
                    }
        if name in self.builtin_catalog:
            spec = self.builtin_catalog[name]
            parameters = [{"label": f"arg{i + 1}"} for i in range(max(spec.required_args, 1 if spec.max_args else 0))]
            for item in spec.keyword_names:
                parameters.append({"label": f"{item}=..."})
            return {
                "label": self._builtin_signature_label(name),
                "documentation": self._describe_name(name),
                "parameters": parameters,
            }
        return None

    def _call_target_at(self, source: str, line: int, character: int) -> tuple[str, int]:
        lines = source.splitlines()
        if line >= len(lines):
            return "", 0
        text = lines[line][:character]
        paren = text.rfind("(")
        if paren < 0:
            return "", 0
        prefix = text[:paren].rstrip()
        end = len(prefix)
        start = end
        while start > 0 and (prefix[start - 1].isalnum() or prefix[start - 1] == "_" or ord(prefix[start - 1]) > 127):
            start -= 1
        target = prefix[start:end]
        active_parameter = text[paren + 1 :].count(",")
        return target, active_parameter

    def _should_probe_repairs(self, source: str, diagnostics: list[VakDiagnostic]) -> bool:
        if diagnostics:
            return True
        probes = ("जबतक", ".apend(", ".append(", "karma ", "pratyagaccha", "return ", "class ")
        return any(item in source for item in probes)

    def _full_document_action(
        self,
        uri: str,
        original_source: str,
        new_source: str,
        *,
        title: str,
        kind: str,
        diagnostics: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        lines = original_source.splitlines()
        end_line = max(len(lines) - 1, 0)
        end_character = len(lines[-1]) if lines else 0
        payload = {
            "title": title,
            "kind": kind,
            "edit": {
                "changes": {
                    uri: [
                        {
                            "range": {
                                "start": {"line": 0, "character": 0},
                                "end": {"line": end_line, "character": end_character},
                            },
                            "newText": new_source,
                        }
                    ]
                }
            },
        }
        if diagnostics:
            payload["diagnostics"] = diagnostics
        return payload


class VakLanguageServer:
    def __init__(self, in_stream=None, out_stream=None) -> None:
        self.in_stream = in_stream or sys.stdin.buffer
        self.out_stream = out_stream or sys.stdout.buffer
        self.documents: dict[str, str] = {}
        self.tools = VakLanguageTools()
        self._shutdown_requested = False

    def process_request(self, message: dict[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        notifications: list[dict[str, Any]] = []

        if method == "initialize":
            result = {
                "capabilities": {
                    "textDocumentSync": 1,
                    "completionProvider": {},
                    "hoverProvider": True,
                    "definitionProvider": True,
                    "documentSymbolProvider": True,
                    "codeActionProvider": True,
                    "signatureHelpProvider": {"triggerCharacters": ["(", ","]},
                }
            }
            return self._response(msg_id, result), notifications

        if method == "shutdown":
            self._shutdown_requested = True
            return self._response(msg_id, None), notifications

        if method == "exit":
            return None, notifications

        if method in {"textDocument/didOpen", "textDocument/didChange"}:
            uri, text = self._update_document(method, params)
            diagnostics = [item.to_lsp() for item in self.tools.analyze_document(text, self._path_from_uri(uri))]
            notifications.append(
                {
                    "jsonrpc": "2.0",
                    "method": "textDocument/publishDiagnostics",
                    "params": {"uri": uri, "diagnostics": diagnostics},
                }
            )
            return None, notifications

        if method == "textDocument/completion":
            uri, text, line, character = self._read_positioned_document(params)
            result = {"isIncomplete": False, "items": self.tools.completion_items(text, line, character)}
            return self._response(msg_id, result), notifications

        if method == "textDocument/hover":
            uri, text, line, character = self._read_positioned_document(params)
            result = self.tools.hover(text, line, character)
            return self._response(msg_id, result), notifications

        if method == "textDocument/documentSymbol":
            text_doc = params.get("textDocument", {})
            uri = text_doc.get("uri", "file:///memory")
            text = self.documents.get(uri, "")
            result = self.tools.document_symbols(text)
            return self._response(msg_id, result), notifications

        if method == "textDocument/definition":
            uri, text, line, character = self._read_positioned_document(params)
            result = self.tools.definition(text, line, character, uri=uri)
            return self._response(msg_id, result), notifications

        if method == "textDocument/codeAction":
            uri, text, _, _ = self._read_positioned_document(params)
            result = self.tools.code_actions(text, filename=self._path_from_uri(uri), uri=uri)
            return self._response(msg_id, result), notifications

        if method == "textDocument/signatureHelp":
            uri, text, line, character = self._read_positioned_document(params)
            result = self.tools.signature_help(text, line, character)
            return self._response(msg_id, result), notifications

        return self._response(msg_id, None), notifications

    def serve_forever(self) -> int:
        while True:
            message = self._read_message()
            if message is None:
                return 0
            response, notifications = self.process_request(message)
            for notification in notifications:
                self._write_message(notification)
            if response is not None:
                self._write_message(response)
            if self._shutdown_requested and message.get("method") == "exit":
                return 0

    def _read_message(self) -> dict[str, Any] | None:
        headers: dict[str, str] = {}
        while True:
            raw = self.in_stream.readline()
            if not raw:
                return None
            line = raw.decode("utf-8").strip()
            if not line:
                break
            key, _, value = line.partition(":")
            headers[key.lower()] = value.strip()

        length = int(headers.get("content-length", "0"))
        if length <= 0:
            return None
        body = self.in_stream.read(length)
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    def _write_message(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self.out_stream.write(header)
        self.out_stream.write(body)
        self.out_stream.flush()

    def _update_document(self, method: str, params: dict[str, Any]) -> tuple[str, str]:
        if method == "textDocument/didOpen":
            text_doc = params.get("textDocument", {})
            uri = text_doc.get("uri", "file:///memory")
            text = text_doc.get("text", "")
        else:
            text_doc = params.get("textDocument", {})
            uri = text_doc.get("uri", "file:///memory")
            text = params.get("contentChanges", [{}])[-1].get("text", self.documents.get(uri, ""))
        self.documents[uri] = text
        return uri, text

    def _read_positioned_document(self, params: dict[str, Any]) -> tuple[str, str, int, int]:
        text_doc = params.get("textDocument", {})
        uri = text_doc.get("uri", "file:///memory")
        position = params.get("position", {})
        text = self.documents.get(uri, "")
        return uri, text, int(position.get("line", 0)), int(position.get("character", 0))

    def _response(self, msg_id: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _path_from_uri(self, uri: str) -> str:
        if uri.startswith("file://"):
            parsed = urlparse(uri)
            path = unquote(parsed.path)
            if len(path) >= 3 and path[0] == "/" and path[2] == ":":
                path = path[1:]
            return str(Path(path))
        return uri


def main() -> int:
    server = VakLanguageServer()
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
