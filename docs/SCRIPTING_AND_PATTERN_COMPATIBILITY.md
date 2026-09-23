# Chimera II OS — Scripting, Regex and Wildcard Compatibility

Chimera II provides a common scripting compatibility layer for shell and scripting languages.

## Shell languages

The registry covers POSIX sh, Bash, Zsh, Ksh, Dash, Csh/Tcsh, Fish, PowerShell, CMD, Nushell, Elvish and Xonsh, plus Python and Perl runtimes. Bash documents quoting, parameters, functions, expansions, redirection, pipelines and script execution as core shell facilities. citeturn0search0turn0search1

## Wildcards

The unified model supports *, ?, bracket expressions and extended patterns where the selected shell supports them. Bash extglob includes ?(), *(), +(), @() and !(). citeturn0search0 Python fnmatch explicitly implements shell-style filename matching separately from regular expressions, while glob performs pathname expansion with *, ? and []. citeturn0search7turn0search8 Perl also provides Unix-shell-like glob expansion. citeturn0search5

## Regex

Regex remains distinct from wildcard/glob syntax. The registry identifies POSIX basic/extended, PCRE-compatible, Python and Perl regex families.

## Runtime policy

Scripts execute with the installed interpreter selected by the shebang or shell dialect. Chimera never claims a runtime exists when it is absent. Privileged operations remain subject to Koronos/Aegis authorization.

## Arabic

Arabic command aliases coexist with English commands. Script grammar remains the grammar of the selected language; translation does not rewrite program syntax.
