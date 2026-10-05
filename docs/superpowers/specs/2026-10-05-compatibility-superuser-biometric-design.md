# Compatibility superuser identities and biometric authentication

Status: proposed design for review  
Repository: `amerhwitat/ChimeraIIOS`  
Target base: `main`

## Goal

Provide the requested administrator identities consistently across ChimeraIIOS native administration and Unix, Linux, Windows, and macOS compatibility modes. Let the installer set passwords for installed systems. In a Live CD session, leave those passwords blank and keep the session ephemeral. Add capability-detected login authentication methods, configured during installation or later from Aurora Desktop Preferences, and synchronize their shared policy and interfaces with the Microkernel and Mobile Edition.

## Identity model

Use three canonical privileged identities with explicit compatibility mappings:

| Identity | Compatibility mapping | Intended use |
| --- | --- | --- |
| `chimera` | ChimeraIIOS native administrator | Native system administration and Aurora settings |
| `root` | Unix, Linux, and macOS root-compatible operations | POSIX compatibility administration |
| `Administrator` | Windows Administrator-compatible operations | Windows compatibility administration |

Each identity maps to a named privileged role through a compatibility adapter. Do not make a typo, case-folding collision, or guest account an administrator. Keep IDs, password hashes, and role mappings separate from ROM metadata and emulator sandbox identities. Do not silently map ordinary ROM/emulator processes into an administrative role.

## Installed system behavior

- Create/configure the three identities during installation and prompt for a password for each one before enabling that identity.
- Allow the user to choose distinct passwords; never require a shared password across modes.
- Store only salted password verifiers using the platform's supported password-hashing facility. Never place plaintext passwords, hashes, recovery material, or test credentials in the repository, logs, crash reports, or exported configuration.
- Permit password changes and account disablement through the native administration interface.
- Apply each identity only to its corresponding compatibility adapter; do not imply that a Chimera `root` mapping creates a real account inside an external Windows or macOS installation.
- Do not enable remote login or network administration as part of this feature. Compatibility adapters must use the host's authenticated privilege broker and must not bypass its access controls.

## Live CD behavior

- Start a nonpersistent Live CD session with empty passwords for the requested privileged identities.
- Make the no-password state explicit in local session status; do not emit secrets or fabricate hashes for empty values.
- Limit passwordless privileged use to the interactive local Live CD session. Disable remote login, remote elevation, and persistent credential creation while running live.
- Keep Live CD changes ephemeral and discard identity/password changes at shutdown unless the user explicitly installs the system.
- On installation from a Live CD, require password setup for all enabled installed privileged identities before writing the installed account database.

## Compatibility and integration

- Extend the existing `include/chimera/security/biometric_auth.hpp`, `src/security/biometric_auth.cpp`, `tools/runtime/chimera-biometric-auth.py`, `system/security/chimera_auth_policy.json`, PAM policy, and Aurora settings contracts; do not create a second independent authentication store. Existing capability-detected method IDs are fingerprint, face, iris, palm, hand geometry, voice, vein, FIDO2/passkey, and smart card/PIV. FIDO2 and smart cards are hardware authenticators, not biometric modalities, but remain available in the unified login-method settings.
- In the installer, let the user configure password and available authentication options for the installed target. In Aurora Desktop Preferences, let an authenticated user enroll, enable, disable, and inspect supported methods at runtime. Require re-authentication with the account password before enrollment or security-policy changes. Preserve username/password recovery.
- Probe actual provider and sensor capability. Show unsupported methods as unavailable; do not expose a setting that reports enabled when no provider can enforce it. Require liveness/anti-spoof capability for face, iris, palm, voice, and vein recognition. Do not treat ordinary 2D camera recognition as a high-assurance login provider.
- Use platform authentication brokers rather than collecting raw biometric samples in Chimera user space: Linux fingerprint through fprintd/PAM where available; Windows through an appropriate Windows Hello/Windows Biometric provider; Android through `BiometricPrompt`; Apple platforms through LocalAuthentication. The provider returns only an authentication result suitable for the requested local login/action. Templates stay under the platform's protected biometric store; never export or synchronize templates between desktop, Mobile Edition, and Microkernel.
- Keep the actual sensor interaction and provider adapters in user space. The Microkernel exposes only the minimum capability-protected authentication IPC boundary and validates a scoped success/failure result; it must not store templates or receive raw sensor data.
- For hosted Android/iOS editions, use the native platform prompt and key store/broker. For bare-metal Mobile Edition, surface only hardware/provider methods that the target device profile can actually support; do not promise a universal fingerprint/face API.
- Reflect shared account IDs, policy schema, authentication-service IPC contract, UI preference schema, docs, and tests in `Mobile Microkernel`, `mobile/mobile-sync.json`, `editions/mobile`, and the existing mobile validation workflows. Commit the desktop, microkernel, and mobile changes together in the reviewed feature branch so the source of truth remains synchronized.
- Add clear installer and native settings flows, with validation and confirmation for each password. Mask input and prevent passwords from entering command-line arguments or environment variables.
- Keep MAME and other emulator processes in the existing sandbox/read-only model. Superuser availability must not weaken media path, wrapper, mount, or license policy.
- Add audit events for successful/failed administrative actions that identify the account and action, never the entered password or verifier.

Official provider constraints to honor include Android's system biometric prompt and authenticator-class capability model, and Apple's LocalAuthentication boundary, which returns an authentication result without exposing stored biometric data. See [Android BiometricPrompt](https://developer.android.com/reference/android/hardware/biometrics/BiometricPrompt), [Apple LocalAuthentication](https://developer.apple.com/documentation/localauthentication), and [Windows biometric APIs](https://learn.microsoft.com/en-us/windows/win32/secbiomet/biometric-service-api-reference).

## Acceptance criteria

- Installer tests confirm all three identities and compatibility role mappings are configured only after password setup; distinct passwords work independently.
- Password verifiers use the platform-supported salted hash path, and searches of logs/config exports/test fixtures show no plaintext credentials or reusable test password.
- Live CD integration tests confirm empty passwords, local-only privileged login, blocked remote login/elevation, nonpersistent state, and required password setup during installation.
- Installer and Aurora preferences tests cover enrollment/configuration of every registered method, provider capability detection, unavailable hardware, re-authentication before enrollment, password recovery, liveness-gated methods, and no exposure of raw samples.
- Android and Apple Mobile Edition builds exercise only their native biometric brokers; the Mobile Microkernel contract receives scoped authentication results but never biometric templates or raw samples.
- Mobile sync validation confirms account, auth-policy, and IPC contract parity across the shared runtime and Microkernel/mobile manifests.
- Tests confirm guest/emulator processes cannot acquire superuser roles and compatibility adapters cannot bypass the host privilege broker.
- Account naming/case collision, disabled identity, invalid password, and failed compatibility adapter paths fail closed and are reported clearly.
- Documentation states which privilege mapping is being used and does not claim that the feature creates accounts in unrelated external OS installations.

## Out of scope

- Creating or changing accounts inside a separately installed Windows, Linux, Unix, or macOS system.
- Enabling SSH, remote desktop administration, network root login, passwordless installed accounts, or shared passwords.
- Replacing the underlying authentication database or bypassing the host OS privilege broker.

