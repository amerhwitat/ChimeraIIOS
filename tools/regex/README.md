# Chimera II GNU BRE/ERE Regular Expression Compatibility

Chimera II exposes a compatibility registry for GNU-style BRE and ERE syntax used by grep, sed, and awk. The registry is derived from the syntax covered by the learnbyexample GNU BRE/ERE cheatsheet:

https://learnbyexample.github.io/gnu-bre-ere-cheatsheet/

## Engines
- grep: BRE by default; ERE with -E; PCRE with -P where supported.
- sed: BRE by default; ERE with -E.
- awk: ERE.
- Chimera's compatibility layer records these as distinct dialects instead of silently changing their semantics.

## Covered syntax
- Anchors: ^, $, \\<, \\>, \\b, \\y, \\B
- Alternation/grouping: |, \\|, (), \\(\\)
- Escaping and literal metacharacters
- Dot and quantifiers: ., ?, *, +, and interval expressions
- Character classes and ranges
- GNU escape sequences
- POSIX named character classes
- Backreferences and replacement references
- sed substitution flags
- sed replacement case conversion
- sed custom delimiters

## Compatibility policy
Regex behavior is engine-, mode-, and locale-dependent. GNU BRE/ERE is not PCRE, and \\d/\\D should not be assumed to mean digits/non-digits in GNU BRE/ERE. Character-class escape behavior also differs between tools.

The registry is metadata for the shell/toolchain. It does not copy the source site's prose or artwork.
