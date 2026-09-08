# Aurora Web Graphics Architecture

Aurora's browser interface uses Three.js as a high-level 3D scene layer over WebGL 2. The native Aurora compositor remains conceptually separate: native Linux uses Wayland/EGL/OpenGL, while the browser uses WebGL, whose API is based on OpenGL ES. This preserves an explicit native-vs-web boundary.

## Performance strategy

- WebGL 2 backend through Three.js `WebGLRenderer`.
- `powerPreference: high-performance` where supported.
- Antialiasing disabled by default for lower GPU bandwidth.
- Device-pixel-ratio capped at 2 to avoid pathological 4K/retina fill-rate costs.
- `setAnimationLoop()` is used for the render loop.
- `BufferGeometry` keeps vertex data in GPU-friendly buffers.
- `InstancedMesh` batches repeated objects into fewer draw calls.
- Resize events update the camera only when the drawing surface changes.
- Avoid per-frame allocation in the hot render path.
- Explicit disposal prevents GPU resource leaks.

## Native graphics correspondence

| Aurora native | Aurora web |
|---|---|
| Wayland surface | Canvas/WebGL surface |
| EGL context | WebGL2 context |
| OpenGL/GLSL | WebGL2/GLSL ES |
| DMA-BUF / zero-copy | Browser-managed GPU resources |
| compositor frame | Three.js render loop |
| GPU buffers | BufferGeometry / InstancedMesh |

The web layer does **not** claim to expose DMA-BUF or native OpenGL directly. Those are native compositor capabilities. The web implementation provides a performance-oriented visualization and architecture-control surface.

## Sources

- Three.js WebGLRenderer: https://threejs.org/docs/pages/WebGLRenderer.html
- Three.js BufferGeometry: https://threejs.org/docs/pages/BufferGeometry.html
- Three.js InstancedMesh: https://threejs.org/docs/pages/InstancedMesh.html
- Khronos WebGL: https://www.khronos.org/webgl/
- Khronos OpenGL Registry: https://registry.khronos.org/OpenGL/
