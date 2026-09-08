// Aurora WebGL bridge: keeps the browser visualization aligned with native OpenGL concepts.
// The browser side uses WebGL 2, which is based on OpenGL ES 3.0 semantics.
export function createAuroraGL(canvas) {
  const gl = canvas.getContext('webgl2', {
    alpha: true,
    antialias: false,
    depth: true,
    powerPreference: 'high-performance',
    desynchronized: true
  });
  if (!gl) throw new Error('Aurora requires WebGL 2');
  return {
    gl,
    resize(width, height) {
      const dpr = Math.min(globalThis.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.floor(width * dpr));
      const h = Math.max(1, Math.floor(height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w; canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
    },
    clear(r=0, g=0, b=0, a=0) {
      gl.clearColor(r, g, b, a);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    },
    dispose() { gl.getExtension('WEBGL_lose_context')?.loseContext(); }
  };
}
