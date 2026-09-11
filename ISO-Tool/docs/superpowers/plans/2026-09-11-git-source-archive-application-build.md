# Git Source, Archive, Application, and Output Pipeline Implementation Plan

**Goal:** Acquire Git/GitHub repositories or source archives, scan them, discover optional applications, compile recognized source, and write ISO/IMG artifacts to user-selected locations.

**Architecture:** Source acquisition normalizes Git/GitHub/archive/local inputs and records provenance. Repository intelligence and application discovery feed the existing deterministic build planner; AI remains advisory. The GUI exposes source and independent output destinations.

**Tasks:** source acquisition with safe archive extraction; application/package discovery with explicit installation authorization; registered build adapters for CMake/Make/Meson/Cargo/npm/Maven/Gradle/.NET/Autotools; GUI source/output controls; mirror implementation and documentation; tests for source classification, traversal rejection, hashes, application discovery, and authorization.

**Global constraints:** never execute arbitrary downloaded scripts; record provenance and checksums; preserve deterministic dependency order; package installation requires explicit authorization; image generation stages files rather than concatenating unrelated image bytes.
