import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';

export class AuroraThree {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setAnimationLoop(() => this.render());
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(55, 1, 0.1, 2000);
    this.camera.position.set(0, 1.5, 8);
    this.clock = new THREE.Clock();
    this.group = new THREE.Group();
    this.scene.add(this.group);

    const geometry = new THREE.IcosahedronGeometry(1, 2);
    const material = new THREE.MeshStandardMaterial({ color: 0x66ccff, roughness: 0.35, metalness: 0.25, wireframe: true });
    this.core = new THREE.Mesh(geometry, material);
    this.group.add(this.core);

    const instanceGeometry = new THREE.BoxGeometry(0.055, 0.055, 0.055);
    const instanceMaterial = new THREE.MeshBasicMaterial({ color: 0x88eaff });
    this.nodes = new THREE.InstancedMesh(instanceGeometry, instanceMaterial, 512);
    const matrix = new THREE.Matrix4();
    for (let i = 0; i < 512; i++) {
      const a = i * 0.37;
      const r = 2.1 + (i % 16) * 0.055;
      matrix.makeTranslation(Math.cos(a) * r, Math.sin(a * 1.37) * r * 0.55, Math.sin(a) * r);
      this.nodes.setMatrixAt(i, matrix);
    }
    this.nodes.instanceMatrix.needsUpdate = true;
    this.group.add(this.nodes);

    const light = new THREE.PointLight(0xffffff, 80, 30);
    light.position.set(2, 4, 6);
    this.scene.add(light);
    this.scene.add(new THREE.AmbientLight(0x406080, 1.2));

    this.resize = this.resize.bind(this);
    window.addEventListener('resize', this.resize, { passive: true });
    this.resize();
  }

  resize() {
    const w = this.canvas.clientWidth || this.canvas.parentElement.clientWidth || innerWidth;
    const h = this.canvas.clientHeight || this.canvas.parentElement.clientHeight || innerHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / Math.max(h, 1);
    this.camera.updateProjectionMatrix();
  }

  render() {
    const t = this.clock.getElapsedTime();
    this.group.rotation.y = t * 0.12;
    this.group.rotation.x = Math.sin(t * 0.17) * 0.08;
    this.core.rotation.z = t * 0.18;
    this.renderer.render(this.scene, this.camera);
  }

  dispose() {
    window.removeEventListener('resize', this.resize);
    this.renderer.setAnimationLoop(null);
    this.renderer.dispose();
    this.group.traverse(o => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach(m => m.dispose());
        else o.material.dispose();
      }
    });
  }
}
