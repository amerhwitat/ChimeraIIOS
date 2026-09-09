# Chimera II Unified Help

Chimera II now defines one documentation namespace for native terminals, Web Terminal, and Aurora.

## Command model

- `man PAGE`
- `man SECTION PAGE`
- `man NAMESPACE:PAGE`
- `apropos KEYWORD`
- `whatis COMMAND`
- `info MENU-ITEM`
- `help COMMAND`
- `chimera-help show PAGE`
- `chimera-help search QUERY`
- `chimera-help sources`
- `chimera-help verify`
- `chimera-help doctor`

## Sources

Linux/POSIX/BSD/System V manuals are indexed from documentation installed on the host. Source-family manifests are in `tools/help/linux_sources.json`; the design intentionally does not copy every distribution's complete manual collection into Git.

Microsoft/Windows/PowerShell documentation is represented as licensed local help where available and official documentation references otherwise. The source policy is recorded in `tools/help/microsoft_sources.json`.

The legacy `web/man_pages.json` catalog remains a migration/compatibility seed. Its current schema is `chimera-man-db/v1` and it already identifies POSIX, Linux, BSD, System V, Bash, Zsh, PowerShell, Windows CMD, and Chimera II sources. 

## Security

Help viewing is read-only. Web and Aurora documentation features must not execute host commands merely to obtain `--help`, and remote Microsoft documentation must not be silently copied into the repository without verified redistribution rights.
