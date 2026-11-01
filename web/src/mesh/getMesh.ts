import type {
  DiscretizedLongBarNode,
  DiscretizedStirrupNode,
  RebarCageMapping,
  SemanticRebarZone,
} from "../data-model.ts";

export function getRebarCageMesh(
  bMm: number,
  hMm: number,
  heightHColMm: number,
  coverMm: number,
  longBarDiaMm: number,
  zones: SemanticRebarZone[]
): {
  stirrups: DiscretizedStirrupNode[];
  longBars: DiscretizedLongBarNode[];
  mapping: RebarCageMapping;
} {
  const zoneToStirrups = new Map<string, number[]>();
  const stirrupToZone = new Map<number, string>();
  const faceToBars = new Map<string, number[]>();
  const stirrups: DiscretizedStirrupNode[] = [];
  const longBars: DiscretizedLongBarNode[] = [];

  const xb = bMm / 2 - coverMm - 10;
  const yb = hMm / 2 - coverMm - 10;
  const coords: [string, number, number][] = [
    ["CORNER_TL", -xb, yb],
    ["MID_TOP", 0, yb],
    ["CORNER_TR", xb, yb],
    ["MID_RIGHT", xb, 0],
    ["CORNER_BR", xb, -yb],
    ["MID_BOT", 0, -yb],
    ["CORNER_BL", -xb, -yb],
    ["MID_LEFT", -xb, 0],
  ];

  const areaLongM2 = (Math.PI * Math.pow(longBarDiaMm / 1000, 2)) / 4;
  const barLenM = (heightHColMm + 400) / 1000;
  const barWeight = 7850 * areaLongM2 * barLenM;

  coords.forEach(([face, x, y], idx) => {
    longBars.push({
      index: idx,
      faceId: face,
      xMm: x,
      yMm: y,
      diameterMm: longBarDiaMm,
      lengthMm: heightHColMm + 400,
      weightKg: barWeight,
    });
    faceToBars.set(face, [idx]);
  });

  const stirrupPerimMm = 2 * (bMm - 2 * coverMm + (hMm - 2 * coverMm)) + 150;
  const perimM = stirrupPerimMm / 1000;

  for (const z of zones) {
    const indices: number[] = [];
    const areaStM2 = (Math.PI * Math.pow(z.stirrupDiameterMm / 1000, 2)) / 4;
    const stWeight = 7850 * areaStM2 * perimM;

    let zCurr = z.zStartMm + z.stirrupSpacingMm;
    while (zCurr <= z.zEndMm) {
      const idx = stirrups.length;
      stirrups.push({
        index: idx,
        zoneId: z.id,
        zMm: zCurr,
        perimeterMm: stirrupPerimMm,
        weightKg: stWeight,
      });
      indices.push(idx);
      stirrupToZone.set(idx, z.id);
      zCurr += z.stirrupSpacingMm;
    }
    zoneToStirrups.set(z.id, indices);
  }

  return {
    stirrups,
    longBars,
    mapping: { zoneToStirrups, stirrupToZone, faceToBars },
  };
}
