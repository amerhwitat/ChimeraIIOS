# Chimera SQL runtime

The database layer uses a dialect-neutral AST and execution planner. T-SQL and PL/SQL compatibility layers translate supported syntax into the Chimera execution model.

The architecture separates:
1. SQL parsing and semantic analysis.
2. Dialect translation.
3. Cost-based planning.
4. Row/column/hybrid execution.
5. Transaction and WAL services.
6. MDM/ER semantic services.
7. CDC/event integration.

Vendor-specific behavior is exposed only through documented compatibility profiles; proprietary database implementations are not copied into Chimera II OS.
