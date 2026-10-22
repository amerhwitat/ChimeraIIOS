# Mobile Edition — visual and functional implementation contract

## Visual target
Use the supplied Mobile Edition reference as the visual acceptance target, not as evidence that implementation already exists.

- Full-viewport aurora/mountain wallpaper with a dark translucent overlay.
- Compact status bar with time/date, connectivity, signal and battery only when real providers expose them.
- Central glass-style identity card with Chimera II OS branding and bilingual English/Arabic copy.
- Status cards for CPU, battery, network, storage and security/boot state. Missing providers must show “Unavailable” or “Not connected”; never fabricate readings.
- Quick actions for Apps, Files, Settings, Terminal, Browser and Store.
- Searchable app launcher, bottom information panels for kernel/services/About, and a persistent bottom dock.
- Responsive layouts for phone portrait/landscape, tablet and desktop; no horizontal overflow.
- Correct RTL Arabic/LTR English, safe-area insets, touch-sized targets, keyboard/focus support, contrast, zoom, screen-reader labels and reduced-motion preferences.

## App registry and launch contract
Generate launcher entries from a machine-readable registry. Each entry needs a stable ID, display name, category, icon, executable launch target, supported platforms, capabilities, implementation status and verification evidence.

Allowed statuses: `implemented`, `partial`, `provider-required`, `planned`, `unavailable`. Only `implemented` may be presented as working, and it must have a real launch target plus a test. Initial first-party entries include Aurora session, Browser, Files, Terminal, Store, Settings, Camera, Gallery, Music, Video, Mail, Calendar and system status. Missing implementations must state the reason, not pretend to launch.

Settings must use a native persistence provider where available. Browser `localStorage` must be labelled browser-local and must not count as native persistence.

## Acceptance checks
1. Screenshot/layout checks at phone portrait, phone landscape, tablet and desktop sizes.
2. RTL/LTR checks, including mixed-direction numbers and labels.
3. Registry schema validation and launch test for every `implemented` entry.
4. Keyboard, touch, focus, contrast, reduced-motion and overflow checks.
5. Live cards consume real providers; absent providers show explicit unavailable states.
6. Persistence survives application restart and is tested separately from browser storage.
7. Release notes distinguish web/mobile shell, native desktop, emulator and bootable ISO.

This contract is not a claim that every app, mobile driver, hardware service or full OS runtime is implemented. An icon, route, compile or static mockup alone is not readiness evidence.
