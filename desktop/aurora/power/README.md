# Aurora Desktop Power, Lock, Screensaver and Sound

This layer defines desktop behavior contracts for Chimera II OS. It provides Windows-style desktop conveniences without copying proprietary implementation.

## Features
- idle detection and configurable automatic screen lock
- screensaver modes and secure Aegis session transition
- AC/battery profiles: balanced, power-saver, performance
- display dim/off and suspend policies
- battery-aware background activity reduction
- desktop and interaction sounds
- mouse single/double/right/middle-click and drag/drop contracts
- Aurora Settings integration
- persistence through Hive and coordination with Koronos/Kore/Aegis

Security-sensitive actions remain governed by Aegis and Koronos. Power saving must never disable security updates or weaken authentication.
