# Aurora biometric authentication

Aurora now has a unified biometric-login contract alongside the normal username/password path.

Supported contracts:
- fingerprint
- face recognition
- iris recognition
- palm recognition
- hand geometry
- voice recognition
- palm/finger vein recognition
- FIDO2/passkeys
- smart cards/PIV

Hardware support is capability-driven. Unsupported sensors remain unavailable rather than being treated as trusted biometric evidence.

## Login policy

1. Username/password remains available.
2. Aurora offers only enrolled methods whose providers report usable hardware.
3. Face, iris, palm, voice and vein providers require liveness/anti-spoofing support.
4. Enrollment requires an existing authenticated credential.
5. Raw biometric samples are not transmitted to remote services.
6. Remote biometric login is disabled by default.
7. Recovery remains possible through the normal password path.

Linux fingerprint support is designed around libfprint/fprintd. fprintd provides fingerprint scanning through D-Bus and a PAM module for login integration. citeturn0search3turn0search7

For facial authentication, an IR/3D-capable provider with liveness detection should be preferred over ordinary 2D webcam recognition. Existing Linux implementations demonstrate PAM integration, but also warn against treating face recognition as the sole high-security authentication method. citeturn0search0turn0search8

The Chimera registry therefore models biometric methods as authentication providers rather than pretending every computer has every sensor.

## Runtime status

The biometric controller is:
tools/runtime/chimera-biometric-auth.py

Examples:
chimera-biometric-auth.py status
chimera-biometric-auth.py enable fingerprint
chimera-biometric-auth.py disable voice

The state is stored under the user's Chimera configuration directory.

## Security model

Biometric verification is local authentication evidence. It is not a replacement for cryptographic credentials, device-bound keys, or administrative recovery credentials.

For high-assurance deployments, combine biometrics with TPM/device-bound credentials, FIDO2/security keys, or passwords according to the site's security policy.
