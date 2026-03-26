# वाक् भाषा - सूत्र विस्तारक (Pāṇinian Macro System)

## Overview

The **Pāṇinian Macro System** (सूत्र विस्तारक) is a compile-time AST transformation system for VakyaLang, inspired by the ancient Sanskrit grammarian **Pāṇini** and his work **Aṣṭādhyāyī**.

This system allows users to define custom syntax at compile-time with **zero runtime overhead**, combining the power of Lisp macros with the elegance of Pāṇini's grammatical rules.

---

## Architecture

### Core Concepts

| Sanskrit Term | English | Description |
|---------------|---------|-------------|
| **सूत्र** (Sūtra) | Thread/Rule | Macro definition - a compile-time transformation rule |
| **अनुवाद** (Anuvāda) | Translation | Expansion template - what the macro expands to |
| **अनुवृत्ति** (Anuvṛtti) | Context Continuation | Inherited context across rules (future feature) |

### Design Philosophy

1. **Compile-time Only**: All macro expansion happens before bytecode generation
2. **Zero Runtime Overhead**: No macro system code in the final bytecode
3. **Hygienic**: Macros don't accidentally capture variables
4. **Composable**: Macros can call other macros (recursive expansion)
5. **Pāṇinian**: Inspired by ancient Indian grammatical traditions

---

## Syntax

### Macro Definition

```vak
सूत्र name(param1, param2, ...):
    अनुवाद -> expansion_template
```

### Components

1. **`सूत्र`** (Sūtra): Keyword to declare a macro
2. **`name`**: Macro name (identifier)
3. **`params`**: Parameter list (comma-separated identifiers)
4. **`अनुवाद`** (Anuvāda): Keyword introducing the expansion template
5. **`->`**: Arrow operator separating keyword from template
6. **`expansion_template`**: AST node to substitute (expression, statement, or block)

---

## Examples

### 1. Simple Arithmetic Macro

```vak
# Define
सूत्र double(x):
    अनुवाद -> x * 2

# Usage (expands to: 5 * 2)
result = double(5)
```

**Expansion Process:**
```
Source:     double(5)
AST:        CallExpr("double", [NumberLiteral(5)])
Match:      Found macro "double" with param ["x"]
Substitute: Replace x with NumberLiteral(5) in "x * 2"
Result:     BinaryExpr(5, '*', 2)
Bytecode:   LOAD 5, LOAD 2, MUL
```

### 2. Multi-parameter Macro

```vak
# Define
सूत्र hypotSq(a, b):
    अनुवाद -> a * a + b * b

# Usage (expands to: 3*3 + 4*4)
result = hypotSq(3, 4)  # = 25
```

### 3. Conditional Macro

```vak
# Define absolute value
सूत्र abs(x):
    अनुवाद -> यदि x < 0 अन्यथा -x अन्यथा x

# Usage (expands to full if-else)
result = abs(-10)  # = 10
```

### 4. Nested Macro Calls

```vak
# Define base macros
सूत्र double(x):
    अनुवाद -> x * 2

# Define macro that uses another macro
सूत्र quadruple(x):
    अनुवाद -> double(double(x))

# Usage (recursive expansion)
result = quadruple(3)
# Expands to: double(double(3))
# Expands to: double(3 * 2)
# Expands to: (3 * 2) * 2
# Result: 12
```

### 5. List Comprehension Macro

```vak
# Define sum of squares
सूत्र sumOfSquares(n):
    अनुवाद -> योग([i * i प्रत्येक चर i अन्तर्गत परास(n)])

# Usage
result = sumOfSquares(5)  # = 0+1+4+9+16 = 30
```

---

## Implementation Details

### File Structure

```
vakyalang-upgrade/runtime/src/
├── tokens.py          # SUTRA, ANUVADA, LARROW token types
├── ast_nodes.py       # SutraDecl, MacroPattern AST nodes
├── lexer.py           # Arrow operator (->) tokenization
├── parser.py          # _sutra_decl() method
├── macro_expander.py  # MacroExpander, SansmaticMacroEngine
├── compiler.py        # Macro expansion phase integration
└── errors.py          # MacroError exception class
```

### Compilation Phases

```
Source Code
    ↓
[Lexer] → Tokens
    ↓
[Parser] → AST (with SutraDecl nodes)
    ↓
[Macro Expander] → Expanded AST ← NEW PHASE
    ↓
[Compiler] → Bytecode
    ↓
[VM] → Execution
```

### Macro Expansion Algorithm

```python
def expand(ast):
    for each node in ast:
        if node is SutraDecl:
            register_macro(node)
            remove from AST
        elif node is CallExpr:
            if callee is registered macro:
                expand_macro(node)  # Recursive expansion
            else:
                expand(node.callee)
                expand(node.args)
        else:
            expand all children
```

### Substitution Process

```python
def substitute(node, env):
    if node is IdentifierExpr:
        return env.get(node.name, node)
    elif node is BinaryExpr:
        return BinaryExpr(
            op=node.op,
            left=substitute(node.left, env),
            right=substitute(node.right, env)
        )
    # ... handle all node types
    else:
        return node  # Literals unchanged
```

---

## Advanced Features

### 1. Sansmatic Integration

The `SansmaticMacroEngine` provides logical validation of macro expansions:

```python
from macro_expander import SansmaticMacroEngine

engine = SansmaticMacroEngine(sansmatic_engine)
expanded_ast = engine.expand_with_proof(ast, context={
    'x': {'type': 'Number'},
    'y': {'type': 'String'}
})
```

**Validation Rules:**
- Type constraints: "Only expand if x is Number"
- Precondition checks: "Only expand if x > 0"
- Postcondition verification: "Result must be positive"

### 2. Anuvṛtti (Context Continuation)

Future feature for carrying context across multiple rules:

```vak
# Rule 1: Establishes context
सूत्र rule1(x):
    अनुवाद -> ...
    # Context: x is positive

# Rule 2: Inherits context from Rule 1
सूत्र rule2(y):
    अनुवाद -> ...  # Can assume x is positive
```

### 3. Pattern Matching

Advanced pattern matching with `MacroPattern`:

```python
@dataclass
class MacroPattern(Node):
    pattern_type: str  # 'identifier', 'expression', 'statement', 'block'
    name: str
    constraints: Optional[Dict[str, Any]]
```

---

## Error Handling

### MacroError Class

```python
class MacroError(VakError):
    """Raised when macro expansion fails."""
    
    # Common errors:
    # - Argument count mismatch
    # - Invalid macro syntax
    # - Infinite recursion detected
    # - Substitution failure
```

### Error Examples

```vak
# Error: Argument count mismatch
सूत्र double(x):
    अनुवाद -> x * 2

double(5, 10)  # MacroError: expects 1 parameter, got 2

# Error: Undefined macro
triple(5)  # Not a macro, treated as regular function call
```

---

## Performance Characteristics

### Compile-time vs Runtime

| Aspect | Traditional Functions | Macros |
|--------|----------------------|--------|
| **Expansion Time** | Runtime | Compile-time |
| **Runtime Overhead** | Function call | None |
| **Code Size** | Single copy | Expanded at each call site |
| **Type Checking** | At call time | At expansion time |
| **Debugging** | Stack traces | Expanded code |

### Trade-offs

**Use Macros When:**
- Need compile-time computation
- Want zero runtime overhead
- Creating domain-specific abstractions
- Eliminating boilerplate code

**Use Functions When:**
- Runtime flexibility needed
- Recursion required
- Code size is concern
- Debugging simplicity preferred

---

## Comparison with Other Systems

### Lisp Macros

| Feature | Lisp Macros | VakyaLang Macros |
|---------|-------------|------------------|
| **Expansion Time** | Compile-time | Compile-time |
| **Syntax** | S-expressions | VakyaLang AST |
| **Hygiene** | Manual (usually) | Automatic |
| **Pattern Matching** | Manual | Built-in |
| **Cultural Heritage** | Western | Pāṇinian |

### C Preprocessor

| Feature | C Macros | VakyaLang Macros |
|---------|----------|------------------|
| **Expansion** | Text substitution | AST transformation |
| **Type Safety** | None | Type-aware |
| **Hygiene** | None | Automatic |
| **Debugging** | Difficult | Easier |

---

## Best Practices

### 1. Keep Macros Simple

```vak
# Good: Simple, clear expansion
सूत्र square(x):
    अनुवाद -> x * x

# Bad: Overly complex
सूत्र complex(x, y, z):
    अनुवाद -> यदि x > 0 अन्यथा y * y + z * z अन्यथा x * x + y * y + z * z
# Use a function instead
```

### 2. Document Expansion

```vak
# Clearly document what the macro expands to
सूत्र double(x):
    # Expands to: x * 2
    अनुवाद -> x * 2
```

### 3. Avoid Side Effects in Expansion

```vak
# Bad: Argument evaluated twice
सूत्र doubleEval(x):
    अनुवाद -> x + x

# Usage: doubleEval(increment())
# Problem: increment() called twice!
```

### 4. Use Descriptive Names

```vak
# Good: Clear intent
सूत्र calculateHypotenuse(a, b):
    अनुवाद -> वर्गमूल(a * a + b * b)

# Bad: Unclear
सूत्र calc(a, b):
    अनुवाद -> वर्गमूल(a * a + b * b)
```

---

## Testing Macros

### Unit Test Example

```vak
# Test simple expansion
सूत्र test_double():
    अनुवाद -> double(5) == 10

# Test nested expansion
सूत्र test_quadruple():
    अनुवाद -> quadruple(3) == 12

# Test conditional expansion
सूत्र test_abs():
    अनुवाद -> abs(-10) == 10
```

---

## Future Enhancements

### Planned Features

1. **Full Anuvṛtti Support**: Context continuation across rules
2. **Block Macros**: Multi-statement expansion templates
3. **Pattern Guards**: Conditional expansion based on patterns
4. **Macro Hygiene**: Automatic variable renaming to prevent capture
5. **Macro Libraries**: Import/export macro definitions
6. **Compile-time Reflection**: Inspect AST during expansion
7. **Incremental Expansion**: Step-by-step expansion debugging

### Research Directions

- Integration with Sansmatic logical proof system
- Type-directed macro expansion
- Automatic parallelization via macros
- Domain-specific language (DSL) creation

---

## Historical Context

### Pāṇini's Aṣṭādhyāyī

**Pāṇini** (circa 500 BCE) composed the **Aṣṭādhyāyī**, a grammatical treatise on Sanskrit consisting of ~4,000 sūtras (rules). Key features:

1. **Sūtra Style**: Extremely concise, rule-based formulation
2. **Anuvṛtti**: Context carries over from previous rules
3. **Meta-rules**: Rules about applying rules
4. **Generative Grammar**: Finite rules → infinite sentences

### Modern Application

This macro system applies Pāṇinian principles to programming:

| Pāṇinian Concept | Programming Analog |
|------------------|-------------------|
| Sūtra (rule) | Macro definition |
| Anuvāda (translation) | Expansion template |
| Anuvṛtti (context) | Lexical scope |
| Prakṛti (base form) | Source code |
| Vikṛti (modified form) | Expanded code |

---

## References

### Primary Sources

1. Pāṇini. **Aṣṭādhyāyī**. (circa 500 BCE)
2. Staal, F. **Universals: Studies in Indian Logic and Linguistics**. (1988)
3. Kiparsky, P. **Pāṇini's Theory of Language**. (1979)

### Technical References

1. Kohlbecker, M. **Syntactic Extensions in Lisp**. (1986)
2. Bawden, A. **Quasiquotation in Lisp**. (1999)
3. Herman, A. **Macros in Multi-Pass Compilers**. (2011)

---

## Author & License

**Author:** Visionary RM (Raj Mitra)  
**Date:** March 17, 2026  
**License:** Open Source (MIT)

*Visionary RM (Raj Mitra)* ⚡  
*"सूत्रं चलति, धर्मं जयति" - The rule moves, dharma wins* 🔥

---

## Quick Start

```vak
# 1. Define a macro
सूत्र square(x):
    अनुवाद -> x * x

# 2. Use the macro
result = square(7)  # Expands to: 7 * 7 = 49

# 3. Compile and run
vakyalang run my_program.vak
```

That's it! You're now using the Pāṇinian Macro System. 🎉
