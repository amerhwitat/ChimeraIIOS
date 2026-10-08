# Chimera II terminal and SQL

Aurora's browser terminal provides a safe in-memory SQL fallback through `sql`, `sqlite`, and `sqlite3`, supporting CREATE TABLE, INSERT, SELECT, SHOW TABLES, DESCRIBE and DROP TABLE. It never accesses host files or a host database.

Shell compatibility covers bash, sh, zsh, fish, dash, ksh, csh, tcsh, cmd, PowerShell and pwsh. Host process execution remains disabled until a sandboxed native terminal service provides PTYs, permissions, a filesystem namespace and a real SQLite backend.
