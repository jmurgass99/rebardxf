import * as THREE from "three";
import type { RebarResult } from "../data-model.ts";

export function createRebarViewer3D(container: HTMLElement): {
  update: (bMm: number, hMm: number, heightHColMm: number, res: RebarResult) => void;
} {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x080d14);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 8000);
  camera.position.set(1200, 2200, 2400);
  camera.lookAt(0, 1600, 0);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  container.appendChild(renderer.domElement);

  const ambient = new THREE.AmbientLight(0xffffff, 0.72);
  const dir = new THREE.DirectionalLight(0xffffff, 0.9);
  dir.position.set(1500, 3000, 2000);
  scene.add(ambient, dir);

  const group = new THREE.Group();
  scene.add(group);

  const resize = () => {
    const w = container.clientWidth || 640;
    const h = container.clientHeight || 480;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  };
  window.addEventListener("resize", resize);
  setTimeout(resize, 0);

  const animate = () => {
    requestAnimationFrame(animate);
    group.rotation.y += 0.003;
    renderer.render(scene, camera);
  };
  animate();

  return {
    update(bMm: number, hMm: number, heightHColMm: number, res: RebarResult) {
      while (group.children.length > 0) group.remove(group.children[0]);

      // Pilar de hormigón transparente
      const colGeo = new THREE.BoxGeometry(bMm, heightHColMm, hMm);
      const colMat = new THREE.MeshStandardMaterial({
        color: 0x94a3b8,
        transparent: true,
        opacity: 0.18,
      });
      const colMesh = new THREE.Mesh(colGeo, colMat);
      colMesh.position.set(0, heightHColMm / 2, 0);
      group.add(colMesh);

      // Barras longitudinales 3D
      res.longBars.forEach((b) => {
        const barGeo = new THREE.CylinderGeometry(
          b.diameterMm / 2,
          b.diameterMm / 2,
          b.lengthMm,
          16
        );
        const barMat = new THREE.MeshStandardMaterial({
          color: 0x0ea5e9,
          metalness: 0.8,
          roughness: 0.3,
        });
        const barMesh = new THREE.Mesh(barGeo, barMat);
        barMesh.position.set(b.xMm, b.lengthMm / 2 - 200, b.yMm);
        group.add(barMesh);
      });

      // Cercos transversales
      const cover = 40;
      const stW = bMm - 2 * cover;
      const stD = hMm - 2 * cover;
      res.stirrups.forEach((s) => {
        const isConf = s.zoneId.includes("CONF");
        const lineMat = new THREE.LineBasicMaterial({
          color: isConf ? 0xf43f5e : 0xeab308,
          linewidth: 2,
        });
        const pts = [
          new THREE.Vector3(-stW / 2, s.zMm, -stD / 2),
          new THREE.Vector3(stW / 2, s.zMm, -stD / 2),
          new THREE.Vector3(stW / 2, s.zMm, stD / 2),
          new THREE.Vector3(-stW / 2, s.zMm, stD / 2),
          new THREE.Vector3(-stW / 2, s.zMm, -stD / 2),
        ];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
        const stirrupLine = new THREE.Line(lineGeo, lineMat);
        group.add(stirrupLine);
      });
    },
  };
}
