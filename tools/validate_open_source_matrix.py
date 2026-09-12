#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LANGUAGE_FILES={
 'c':'applications/c/chm_application.h','cpp':'applications/cpp/chm_application.hpp','rust':'applications/rust/chm_applications.rs','python':'applications/python/chimera_applications.py','java':'applications/java/chimera/applications/Application.java','csharp':'applications/csharp/ChimeraApplications.cs','kotlin':'applications/kotlin/ChimeraApplications.kt','swift':'applications/swift/ChimeraApplications.swift','typescript':'applications/typescript/chimera-applications.ts','dart':'applications/dart/chimera_applications.dart'}
missing=[(lang,path) for lang,path in LANGUAGE_FILES.items() if not (ROOT/path).is_file()]
if missing:
    raise SystemExit('missing language bindings: '+', '.join(f'{a}:{b}' for a,b in missing))
print(f'validated {len(LANGUAGE_FILES)} language bindings')
