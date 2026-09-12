# Web Implementations

The repository now has a separated `web/` layer for browser JavaScript, TypeScript contracts, PHP service boundaries and PWA caching. The web layer is an integration/visualization surface and does not replace Koronos, Mobile Microkernel, Spit Fire, Jasper or native services.

## Standards
- ES modules and browser Web APIs
- TypeScript for typed contracts
- PHP standalone JSON endpoints
- PWA/service-worker offline caching
- Future WebAssembly modules use explicit capability boundaries

The browser layer should communicate with native/runtime components through documented APIs rather than direct privileged access.