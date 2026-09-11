# ISO-Tool integration: fail-forward and live details

ISO-Tool jobs use fail-forward isolation: an independent compiler, assembler, scanner, documentation, or boot-artifact runtime error is recorded with its type/message, the job is marked failed/skipped, cumulative progress advances, and the next independent job continues.

This behavior is visible in the application window through a live details/log section plus a cumulative progress bar and current-status text. Python/Tkinter, C# WPF, and VC++ Win32 front ends expose this operational view.

Fail-forward does not suppress failures or bypass safety. Fatal authorization, staging, image-integrity, or physical-disk safety conditions may stop the operation. All recoverable failures remain in the final report.

Canonical implementation: `amerhwitat/nlp/ISO-Tool/`.
