**Sanskrit Vakya Universal Codex**

The Sanskrit Vakya Universal Codex is Vak's modular "book and pages"
translation system. It is not a second compiler. It is a validated transform
spine that routes source through a selected page, emits Vak, and then checks
that emitted Vak with the real Vak frontend/compiler before trusting it.

## Core Contract

Codex core lives in:

- `runtime/src/codex/core.py`
- `runtime/src/codex/models.py`
- `runtime/src/codex/page.py`
- `runtime/src/codex/vak_runtime.py`

Every page exposes a stable manifest:

- `name`
- `description`
- `priority`
- `kind`
- `chapter`
- `chapter_title`
- `chapter_order`
- `capabilities`
- `extensions`
- `emits_vak`
- `experimental`
- `module_path` for `.vak` pages
- `max_fixpoint_passes`

Every result exposes a structured model:

- `source_kind`
- `detected_constructs`
- `applied_rules`
- `rejected_rules`
- `confidence`
- `validation`
- `validation_history`

## Book and Chapters

Codex is explicitly organized as a book with chapters.

Current main chapters:

- `vak_core`
  - `vak_legacy`
  - `vak`
- `bridges`
  - `english_vak`
- `math_logic`
  - `math_logic`
- `sanskrit_notation`
  - `sanskrit_notation`
- `vak_native`
  - `vak_native`
  - `vak_legacy_native`
  - `math_logic_native`
  - `sanskrit_notation_native`
  - `english_vak_native`

Current experimental chapters:

- `experimental_systems`
  - `c_subset`
  - `rust_subset`
- `experimental_language`
  - `natural_language`

Chapter listing is available through:

- Python API: `codex.list_chapters()`
- Vak builtin: `कोडेक्स_अध्याय()`
- CLI: `vak.py --codex-chapters`
- TUI Codex mode: `chapters`

Confidence is always one of:

- `safe_auto_fix`
- `suggest_only`
- `do_not_touch`

## Validation Model

Codex uses fixed-point validation for Vak-emitting pages:

1. page transform
2. Vak lex/parse/compile validation
3. accept or reject the pass
4. rerun until stable or `max_fixpoint_passes`

If a later pass regresses validation or confidence, it is rejected and the
best validated result is kept.

## Main Page Families

Safe pages live in main:

- `vak`
  Canonical Vak compatibility and normalization page.
- `vak_legacy`
  Old/drifted Vak compatibility page.
- `english_vak`
  English/Python-style bridge page.
- `math_logic`
  Symbolic logic and math notation page.
- `sanskrit_notation`
  Transliterated Sanskrit programming notation page.

Real `.vak` pages are first-class too:

- `vak_native`
- `vak_legacy_native`
- `math_logic_native`
- `sanskrit_notation_native`
- `english_vak_native`

Vak-native pages live under:

- `runtime/codex_pages`

They export metadata constants such as:

- `CODEX_PAGE_NAME`
- `CODEX_PAGE_DESCRIPTION`
- `CODEX_PAGE_PRIORITY`
- `CODEX_PAGE_KIND`
- `CODEX_PAGE_CAPABILITIES`
- `CODEX_PAGE_EMITS_VAK`
- `CODEX_PAGE_EXTENSIONS`
- `CODEX_PAGE_HINTS`
- `CODEX_PAGE_MAX_FIXPOINT_PASSES`

Vak page hooks:

- `codex_probe(source, filename)`
- `codex_transform(source, filename)`

## Branch Page Families

Experimental pages live in branches.

Current branch page pack:

- branch: `universal_codex_lab`
- pages:
  - `python_to_vak_experimental`
  - `javascript_to_vak_experimental`
  - `pseudocode_to_vak_experimental`
  - `c_subset`
  - `rust_subset`
  - `natural_language`

The same branch now also vendors the full `codex-system1` page pack inside
VakLang. Those integrated pages are exposed with a `codex_system_` prefix so
they do not collide with VakLang's stronger main pages. Examples:

- `codex_system_python_to_vak`
- `codex_system_javascript_to_vak`
- `codex_system_api_generator`
- `codex_system_cli_generator`
- `codex_system_webapp_generator`
- `codex_system_grammar_engine`
- `codex_system_lexer_generator`
- `codex_system_knowledge_graph`
- `codex_system_bytecode_decoder`
- `codex_system_decompiler_page`
- `codex_system_vak_native`

Their chapters are likewise namespaced, for example:

- `codex_system_bridges`
- `codex_system_math_logic`
- `codex_system_sanskrit_notation`
- `codex_system_translators`
- `codex_system_generators`
- `codex_system_language_tools`
- `codex_system_knowledge_engine`

This is a full branch-pack integration, not a mainline promotion. VakLang's
existing core pages remain the default/stable ones, and the integrated
`codex_system_*` pages stay experimental until they clear promotion gates.

These are intentionally suggestive/experimental rather than guaranteed.

Editor surfaces currently expose Codex as safe whole-document actions. That
means the current LSP/TUI integration can suggest or apply page transforms, but
it does not pretend to offer arbitrary semantic refactors.

## Vak Integration

Codex is available through:

- Python API:
  - `from runtime.src.codex import build_default_codex`
- interpreter API:
  - `VakInterpreter.codex_source(...)`
- CLI:
- `vak.py --codex-pages`
- `vak.py --codex-chapters`
- `vak.py --codex input output`
  - `vak.py --codex input output --codex-page vak`
- Vak builtins:
  - `कोडेक्स(source, page = "auto", filename = शून्य)`
- `कोडेक्स_रिपोर्ट(...)`
- `कोडेक्स_विवरण(...)`
- `कोडेक्स_पृष्ठ()`
- `कोडेक्स_अध्याय()`

This means `.vak` pages and normal Vak programs can invoke the Codex directly.

## TUI Workspace

Vak TUI now has a dedicated Codex workspace:

- mode: `codex`
- commands:
  - `load <path>`
  - `chapters`
  - `pages`
  - `page <name|auto>`
  - `branches [name...]`
  - `analyze`
  - `report`
  - `diff`
  - `show original|current`
  - `apply [path]`
  - `reject`

This gives Codex the same practical workflow that `रूपान्तर` already had.

## Stress Corpus

Codex corpus cases live in:

- `stress/codex_corpus`

The corpus currently covers:

- legacy Vak
- English bridge input
- math/logic notation
- transliterated Sanskrit notation
- C subset branch page
- Rust subset branch page
- deterministic natural-language branch page

## Design Boundary

The Codex is Vak-first and validation-driven.

It is not a claim that Vak now perfectly translates every language. The safe
contract is:

- deterministic pages may auto-transform
- lower-confidence pages must report `suggest_only`
- unsafe or blocked pages must report `do_not_touch`
- experimental foreign-language pages stay in branches until proven

Promotion policy is documented in:

- `docs/universal_codex_promotion.md`
