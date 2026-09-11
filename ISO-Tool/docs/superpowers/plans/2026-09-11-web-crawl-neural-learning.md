# ISO-Tool Web Crawl + Neural Learning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans (recommended) to implement this plan task-by-task.

**Goal:** Add safe integrated web search/crawling and repository-learning with RNN/LLM-ready inference to every ISO-Tool language implementation.

**Architecture:** Python is the reference implementation with standard-library HTTP/HTML/robots handling and optional PyTorch RNN/Transformer adapters. Java, C#/.NET and C++ provide dependency-light parity engines. All implementations share JSON feature names, provenance and safety rules.

**Tech Stack:** Python 3/Tkinter; optional PyTorch; Java 17/Swing; C#/.NET 6/WPF; C++20/Win32; JSON; HTTP(S); RFC 9309.

**Global Constraints:** Respect robots.txt; treat web content as untrusted evidence; cache robots.txt for no more than 24 hours unless unreachable; never execute arbitrary downloaded scripts; preserve provenance; keep the existing ISO pipeline authoritative; neural/LLM inference cannot silently authorize execution.

**Tasks:**
1. Create Python web/search/learning/neural engines and offline tests.
2. Expand the shared GUI feature manifest and wire all four GUIs.
3. Create Java web-learning engine and tests.
4. Create C#/.NET web-learning engine and tests.
5. Create C++ web-learning engine and add it to the GUI project.
6. Update documentation, README and CI.
7. Synchronize all changes with the canonical NLP ISO-Tool implementation.
