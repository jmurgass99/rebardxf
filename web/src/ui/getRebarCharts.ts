import type { RebarResult } from "../data-model.ts";

export function renderCrossSectionChart(
  canvas: HTMLCanvasElement,
  bMm: number,
  hMm: number,
  res: RebarResult
): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const cx = 36 + (w - 52) / 2;
  const cy = 16 + (h - 38) / 2;
  const scale = Math.min((w - 110) / bMm, (h - 60) / hMm);

  const bw = bMm * scale;
  const bh = hMm * scale;

  ctx.fillStyle = "rgba(100,116,139,0.3)";
  ctx.fillRect(cx - bw / 2, cy - bh / 2, bw, bh);
  ctx.strokeStyle = "#94a3b8";
  ctx.strokeRect(cx - bw / 2, cy - bh / 2, bw, bh);

  // Cercos interiores
  const cover = 40 * scale;
  ctx.strokeStyle = "#f43f5e";
  ctx.lineWidth = 1.8;
  ctx.strokeRect(cx - bw / 2 + cover, cy - bh / 2 + cover, bw - 2 * cover, bh - 2 * cover);

  // Barras longitudinales
  res.longBars.forEach((b) => {
    const px = cx + b.xMm * scale;
    const py = cy - b.yMm * scale;
    ctx.fillStyle = "#0ea5e9";
    ctx.beginPath();
    ctx.arc(px, py, Math.max(3, (b.diameterMm * scale) / 2), 0, 2 * Math.PI);
    ctx.fill();
  });

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`Sección ${bMm}x${hMm} mm — 8∅${res.longBars[0]?.diameterMm ?? 20}`, 42, 30);
}

export function renderWeightScheduleChart(canvas: HTMLCanvasElement, res: RebarResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const total = Math.max(res.totalSteelWeightKg, 1);
  const wLong = res.longitudinalWeightKg;
  const wStir = res.stirrupWeightKg;

  const bLong = (wLong / total) * (w - 90);
  const bStir = (wStir / total) * (w - 90);

  ctx.fillStyle = "#0ea5e9";
  ctx.fillRect(50, 60, bLong, 26);
  ctx.fillStyle = "#f43f5e";
  ctx.fillRect(50, 100, bStir, 26);

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`Longitudinal: ${wLong.toFixed(1)} kg (${((wLong / total) * 100).toFixed(0)}%)`, 50, 52);
  ctx.fillText(`Transversal: ${wStir.toFixed(1)} kg (${((wStir / total) * 100).toFixed(0)}%)`, 50, 95);
  ctx.fillText(`Peso total de acero: ${total.toFixed(1)} kg | Anclaje l_b = ${res.anchorageLengthMm.toFixed(0)} mm`, 42, h - 10);
}
