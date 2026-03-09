# वाक् भाषा — व्याकरण विनिर्देश
# Vāk Language — Formal Grammar Specification
# Version 1.0.0 · Author: Raj Mitra · © 2026 · AGPL v3

---

## १. परिचय (Introduction)

वाक् (Vāk) is a general-purpose, dynamically-typed, interpreted programming
language whose entire syntax is expressed in Sanskrit Devanagari script.  
It draws on Pāṇini's grammatical tradition for structural regularity, and
on the Nyāya school for logical primitives.

The language is fully functional. Every keyword, operator name, and built-in
identifier is a valid Sanskrit word with a precise meaning.

---

## २. वर्ण-समूह (Character Set)

वाक् source files are UTF-8 encoded.  
Valid characters include:

- **Devanagari block** U+0900–U+097F — for keywords and identifiers
- **ASCII** — for operators, delimiters, and optionally identifiers
- **Devanagari digits** ०१२३४५६७८९ — interchangeable with ASCII 0–9

---

## ३. शब्द-चिह्न (Tokens)

### ३.१ संख्या साहित्य (Number Literals)

```
number     → devanagari_digit+ ('.' devanagari_digit+)?
           | ascii_digit+       ('.' ascii_digit+)?

devanagari_digit → ० | १ | २ | ३ | ४ | ५ | ६ | ७ | ८ | ९
```

Both `४२` and `42` are identical. Both `३.१४` and `3.14` are identical.

### ३.२ तार साहित्य (String Literals)

```
string     → '"' char* '"'
           | "'" char* "'"

char       → any_unicode_except_quote
           | '\n' | '\t' | '\\' | '\"' | "\'"
```

### ३.३ बूलियन और शून्य (Boolean & Null)

| शब्द     | अर्थ    | Value   |
|----------|---------|---------|
| `सत्य`   | truth   | `true`  |
| `असत्य`  | untruth | `false` |
| `शून्य`  | zero    | `null`  |

### ३.४ पहचानकर्ता (Identifiers)

```
identifier → id_start id_part*

id_start   → devanagari_letter | ascii_letter | '_'
id_part    → devanagari_letter | devanagari_digit
           | ascii_letter | ascii_digit | '_'
```

Identifiers are case-sensitive. Keywords cannot be used as identifiers.

### ३.५ टिप्पणियाँ (Comments)

```
comment    → '#' rest_of_line
           | 'टीका' rest_of_line
```

### ३.६ इंडेंटेशन (Indentation)

वाक् uses **significant whitespace** (Python-style).  
Each block is introduced by `:` and delimited by consistent indentation.  
4 spaces = 1 tab. Mixed indentation within one block is an error.

---

## ४. मूलशब्द (Keywords)

| देवनागरी          | IAST            | Meaning          | Role         |
|--------------------|-----------------|------------------|--------------|
| `चर`               | cara            | moving/variable  | var decl     |
| `स्थिर`            | sthira          | stable           | const decl   |
| `कर्म`             | karma           | action/function  | func decl    |
| `वर्ग`             | varga           | category/class   | class decl   |
| `प्रत्यागच्छ`      | pratyāgaccha    | return/come back | return stmt  |
| `यदि`              | yadi            | if               | conditional  |
| `अन्यत्`           | anyat           | otherwise        | elif         |
| `अन्यथा`           | anyathā         | in another way   | else         |
| `यावत्`            | yāvat           | as long as       | while loop   |
| `प्रत्येक`         | pratyek         | each/every       | for loop     |
| `अन्तर्गत`         | antargata       | within/in        | loop in      |
| `विराम`            | virāma          | stop/pause       | break        |
| `अग्रे`            | agre            | forward          | continue     |
| `मुद्रय`           | mudraya         | imprint/print    | print stmt   |
| `और`               | aur             | and              | logical and  |
| `अथवा`             | athavā          | or               | logical or   |
| `न`                | na              | no/not           | logical not  |
| `सत्य`             | satya           | truth            | true literal |
| `असत्य`            | asatya          | untruth          | false literal|
| `शून्य`            | śūnya           | zero/void        | null literal |
| `प्रयत्न`          | prayatna        | attempt/try      | try block    |
| `दोष`              | doṣa            | fault/error      | catch block  |
| `अन्ततः`           | antataḥ         | ultimately       | finally      |
| `उत्क्षिप`         | utkṣipa         | throw/hurl       | throw stmt   |
| `आयात`             | āyāta           | import/bring in  | import       |
| `से`               | se              | from             | from import  |
| `नव`               | nava            | new              | new instance |
| `स्वयं`            | svayam          | oneself/self     | self ref     |
| `अभिभावक`          | abhibhāvaka     | parent/guardian  | super ref    |

---

## ५. व्याकरण (Grammar — EBNF)

```ebnf
program     = { stmt } EOF ;

stmt        = var_decl
            | const_decl
            | func_decl
            | class_decl
            | if_stmt
            | while_stmt
            | for_stmt
            | return_stmt
            | print_stmt
            | break_stmt
            | continue_stmt
            | try_stmt
            | throw_stmt
            | import_stmt
            | expr_stmt ;

var_decl    = "चर" IDENT [ "=" expr ] NEWLINE ;
const_decl  = "स्थिर" IDENT "=" expr NEWLINE ;

func_decl   = "कर्म" IDENT "(" param_list ")" ":" block ;
param_list  = [ IDENT [ "=" expr ] { "," IDENT [ "=" expr ] } ] ;

class_decl  = "वर्ग" IDENT [ "(" IDENT ")" ] ":" class_body ;
class_body  = NEWLINE INDENT { func_decl } DEDENT ;

if_stmt     = "यदि" expr ":" block
              { "अन्यत्" expr ":" block }
              [ "अन्यथा" ":" block ] ;

while_stmt  = "यावत्" expr ":" block ;

for_stmt    = "प्रत्येक" [ "चर" ] IDENT "अन्तर्गत" expr ":" block ;

return_stmt = "प्रत्यागच्छ" [ expr ] NEWLINE ;
print_stmt  = "मुद्रय" expr { "," expr } NEWLINE ;
break_stmt  = "विराम" NEWLINE ;
continue_stmt = "अग्रे" NEWLINE ;
throw_stmt  = "उत्क्षिप" expr NEWLINE ;

try_stmt    = "प्रयत्न" ":" block
              [ "दोष" [ IDENT ] ":" block ]
              [ "अन्ततः" ":" block ] ;

import_stmt = "आयात" IDENT NEWLINE
            | "आयात" IDENT "से" IDENT NEWLINE ;

expr_stmt   = expr NEWLINE ;

block       = NEWLINE INDENT { stmt } DEDENT
            | stmt ;          (* inline single statement *)

expr        = assignment ;
assignment  = or_expr [ ( "=" | "+=" | "-=" | "*=" | "/=" ) assignment ] ;
or_expr     = and_expr { "अथवा" and_expr } ;
and_expr    = not_expr { "और" not_expr } ;
not_expr    = "न" not_expr | compare ;
compare     = additive { cmp_op additive } ;
cmp_op      = "==" | "!=" | "<" | ">" | "<=" | ">=" | "अन्तर्गत" ;
additive    = multiplicative { ( "+" | "-" ) multiplicative } ;
multiplicative = power { ( "*" | "/" | "//" | "%" ) power } ;
power       = unary [ "**" power ] ;
unary       = "-" unary | call ;
call        = primary { "(" arg_list ")" | "." IDENT | "[" expr "]" } ;
arg_list    = [ (IDENT "=" expr | expr) { "," (IDENT "=" expr | expr) } ] ;

primary     = NUMBER | STRING | "सत्य" | "असत्य" | "शून्य"
            | IDENT | "(" expr ")"
            | "[" [ expr { "," expr } ] "]"           (* list *)
            | "{" [ pair { "," pair } ] "}"            (* dict *)
            | "नव" IDENT "(" arg_list ")" ;

pair        = expr ":" expr ;
```

---

## ६. प्रकार प्रणाली (Type System)

वाक् is **dynamically typed**.  Types are checked at runtime.

| वाक् प्रकार  | अर्थ        | Python equivalent |
|--------------|-------------|-------------------|
| `पूर्णांक`   | integer     | `int`             |
| `दशमलव`     | decimal     | `float`           |
| `तार`        | string      | `str`             |
| `बूलियन`    | boolean     | `bool`            |
| `सूची`       | list        | `list`            |
| `शब्दकोश`   | dictionary  | `dict`            |
| `शून्य`      | null        | `None`            |
| `कर्म`       | function    | `function`        |
| `वर्ग`       | class       | `class`           |

---

## ७. अन्तर्निर्मित कार्य (Built-in Functions)

| कार्य           | अर्थ           | Equivalent  |
|-----------------|----------------|-------------|
| `दीर्घता(x)`    | length         | `len(x)`    |
| `प्रकार(x)`     | type of x      | `type(x)`   |
| `पूर्णांक_कर(x)` | to integer    | `int(x)`    |
| `दशमलव_कर(x)`  | to float       | `float(x)`  |
| `पाठ_कर(x)`    | to string      | `str(x)`    |
| `प्रवेश(prompt)` | user input    | `input()`   |
| `परास(n)`       | range 0..n-1   | `range(n)`  |
| `परास(a,b)`     | range a..b-1   | `range(a,b)`|
| `योग(सूची)`    | sum of list    | `sum()`     |
| `अधिकतम(...)`  | maximum        | `max()`     |
| `न्यूनतम(...)`  | minimum        | `min()`     |
| `क्रमबद्ध(x)`  | sorted copy    | `sorted()`  |
| `उलटो(x)`      | reversed       | `reversed()`|
| `वर्गमूल(x)`   | square root    | `sqrt(x)`   |
| `परम(x)`        | absolute value | `abs(x)`    |
| `जोड़ो(l, x)`  | append to list | `l.append(x)`|
| `विभाजन(s, d)` | split string   | `s.split(d)`|
| `संयोग(l, s)`  | join list      | `s.join(l)` |
| `कुंजियाँ(d)`  | dict keys      | `d.keys()`  |
| `मान(d)`        | dict values    | `d.values()`|
| `दृढ़ता(cond)` | assert         | `assert`    |
| `निर्गम(code)` | exit program   | `exit()`    |

### अन्तर्निर्मित स्थिरांक (Built-in Constants)

| स्थिरांक           | अर्थ        | Value         |
|--------------------|-------------|---------------|
| `पाई`              | π           | 3.14159…      |
| `प्रकृतिक_आधार`   | e (Euler)   | 2.71828…      |

---

## ८. संचालन प्राथमिकता (Operator Precedence)

Higher number = higher precedence.

| स्तर | संचालक                         | साहचर्य       |
|------|--------------------------------|---------------|
| 1    | `=` `+=` `-=` `*=` `/=`       | right         |
| 2    | `अथवा`                         | left          |
| 3    | `और`                           | left          |
| 4    | `न`                            | right (unary) |
| 5    | `==` `!=` `<` `>` `<=` `>=` `अन्तर्गत` | left |
| 6    | `+` `-`                        | left          |
| 7    | `*` `/` `//` `%`               | left          |
| 8    | `**`                           | right         |
| 9    | `-` (unary)                    | right         |
| 10   | `()` `.` `[]`                  | left          |

---

## ९. उदाहरण कार्यक्रम (Example Programs)

### ९.१ फैक्टोरियल (Factorial)

```vak
कर्म भाज्यफल(न):
    यदि न <= १:
        प्रत्यागच्छ १
    प्रत्यागच्छ न * भाज्यफल(न - १)

प्रत्येक चर इ अन्तर्गत परास(१, ११):
    मुद्रय पाठ_कर(इ) + "! =", भाज्यफल(इ)
```

### ९.२ बुलबुला क्रमीकरण (Bubble Sort)

```vak
कर्म बुलबुला_क्रम(सूची):
    चर न = दीर्घता(सूची)
    प्रत्येक चर इ अन्तर्गत परास(न):
        प्रत्येक चर ज अन्तर्गत परास(न - इ - १):
            यदि सूची[ज] > सूची[ज + १]:
                चर अस्थाई = सूची[ज]
                सूची[ज]     = सूची[ज + १]
                सूची[ज + १] = अस्थाई
    प्रत्यागच्छ सूची

चर अव्यवस्थित = [६४, ३४, २५, १२, २२, ११, ९०]
मुद्रय "क्रमबद्ध:", बुलबुला_क्रम(अव्यवस्थित)
```

---

## १०. अनुज्ञप्ति (License)

The वाक् language specification is released under **Apache License 2.0**.  
The वाक् runtime and interpreter are released under **GNU AGPL v3**.  
Copyright © 2026 Raj Mitra. All rights reserved.

> "वाक् वै ब्रह्म" — Speech is indeed Brahman (the universal principle).  
> — Aitareya Āraṇyaka
