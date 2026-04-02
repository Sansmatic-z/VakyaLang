from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from runtime.src.compiler import Compiler
from runtime.src.errors import CompileError, LexerError, ParseError
from runtime.src.interpreter import VakInterpreter
from runtime.src.lexer import Lexer
from runtime.src.parser import Parser
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

    def to_lsp(self) -> dict[str, Any]:
        zero_line = max(self.line - 1, 0)
        return {
            "range": {
                "start": {"line": zero_line, "character": 0},
                "end": {"line": zero_line, "character": 200},
            },
            "severity": self.severity,
            "source": self.source,
            "message": self.message,
        }


class VakLanguageTools:
    def __init__(self) -> None:
        self.interpreter = VakInterpreter()
        self.keyword_docs = dict(KEYWORD_DOCS)
        self.builtin_docs = dict(BUILTIN_DOCS)
        self._builtins = sorted(self.interpreter.vm.builtins.keys())
        self._keyword_names = sorted(KEYWORDS.keys())

    def analyze_document(self, source: str, filename: str = "<memory>") -> list[VakDiagnostic]:
        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            compiler = Compiler(source_path=filename)
            compiler.compile(ast)
            return []
        except (LexerError, ParseError, CompileError) as error:
            return [VakDiagnostic(getattr(error, "line", 0) or 1, f"{filename}: {error}")]
        except Exception as error:
            return [VakDiagnostic(1, f"Internal tooling error: {error}", source="vak-tooling")]

    def completion_items(self, source: str, line: int, character: int) -> list[dict[str, Any]]:
        prefix = self._identifier_prefix(source, line, character)
        names = self._keyword_names + self._builtins
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        for name in names:
            if prefix and not name.startswith(prefix):
                continue
            if name in seen:
                continue
            seen.add(name)
            items.append(
                {
                    "label": name,
                    "kind": 14 if name in self._keyword_names else 3,
                    "detail": "keyword" if name in self._keyword_names else "builtin",
                    "documentation": self._describe_name(name),
                }
            )
        return items[:100]

    def hover(self, source: str, line: int, character: int) -> dict[str, Any] | None:
        word = self._word_at(source, line, character)
        if not word:
            return None
        description = self._describe_name(word)
        if description is None:
            return None
        return {
            "contents": {
                "kind": "markdown",
                "value": f"**{word}**\n\n{description}",
            }
        }

    def document_symbols(self, source: str) -> list[dict[str, Any]]:
        ast = self._parse_program(source)
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
        ast = self._parse_program(source)
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

    def _parse_program(self, source: str) -> Program | None:
        try:
            return Parser(Lexer(source).tokenize()).parse()
        except Exception:
            return None

    def _describe_name(self, name: str) -> str | None:
        if name in self.keyword_docs:
            return self.keyword_docs[name]
        if name in self.builtin_docs:
            return self.builtin_docs[name]
        if name in self._builtins:
            return "Vak builtin available at runtime."
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
            return str(Path(uri[7:]))
        return uri


def main() -> int:
    server = VakLanguageServer()
    return server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
