// Aurora WebGL bridge: keeps the browser visualization aligned with native OpenGL concepts.
// WebGL 2 follows OpenGL ES 3.0 semantics; it is not a native EGL/OpenGL context.
export function createAuroraGL(canvas, callbacks = {}) {
  const gl = canvas.getContext('webgl2', {
    alpha: true,
    antialias: false,
    depth: true,
    powerPreference: 'high-performance',
    desynchronized: true
  });
  if (!gl) throw new Error('Aurora requires WebGL 2');

  let contextLost = false;
  let disposed = false;
  const onLost = event => {
    event.preventDefault();
    contextLost = true;
    callbacks.onContextLost?.(event);
  };
  const onRestored = event => {
    contextLost = false;
    callbacks.onContextRestored?.(gl, event);
  };
  canvas.addEventListener('webglcontextlost', onLost, false);
  canvas.addEventListener('webglcontextrestored', onRestored, false);

  return {
    gl,
    canvas,
    isContextLost() { return contextLost || gl.isContextLost(); },
    resize(width, height) {
      if (disposed || contextLost) return false;
      const dpr = Math.min(globalThis.devicePixelRatio || 1, 2);
      const w = Math.max(1, Math.floor(width * dpr));
      const h = Math.max(1, Math.floor(height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
        gl.viewport(0, 0, w, h);
      }
      return true;
    },
    clear(r = 0, g = 0, b = 0, a = 0) {
      if (disposed || contextLost) return false;
      gl.clearColor(r, g, b, a);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      return true;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      canvas.removeEventListener('webglcontextlost', onLost, false);
      canvas.removeEventListener('webglcontextrestored', onRestored, false);
      gl.getExtension('WEBGL_lose_context')?.loseContext();
    }
  };
}
