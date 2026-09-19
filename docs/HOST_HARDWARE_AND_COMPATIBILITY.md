# Host Hardware, Drivers, Security and Compatibility

Aurora exposes Hardware & Drivers and System & Services panels. The scanner normalizes Linux, Windows and macOS inventory into a common schema.

Koronos prefers native drivers. Linux source is adapted through the Linux device-model compatibility layer; Windows WDM/WDF is represented through isolated PE/user-mode compatibility; macOS DriverKit/System Extensions are represented as user-space adapters. Current Apple documentation describes DriverKit drivers as user-space and System Extensions as the installation/management mechanism.

Security policies are normalized rather than treated as identical: Linux SELinux/AppArmor/DAC/capabilities; Windows security descriptors/tokens/integrity/code-integrity; macOS SIP/Gatekeeper/signing/entitlements/TCC/DriverKit.

Driver updates are discover/verify/diff/authorize/install/rollback. No arbitrary downloaded installer is silently executed.
