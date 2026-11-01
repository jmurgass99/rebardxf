export interface SemanticRebarZone {
  id: string;
  zStartMm: number;
  zEndMm: number;
  stirrupSpacingMm: number;
  stirrupDiameterMm: number;
}

export interface RebarCageMapping {
  zoneToStirrups: Map<string, number[]>;
  stirrupToZone: Map<number, string>;
  faceToBars: Map<string, number[]>;
}

export interface DiscretizedStirrupNode {
  index: number;
  zoneId: string;
  zMm: number;
  perimeterMm: number;
  weightKg: number;
}

export interface DiscretizedLongBarNode {
  index: number;
  faceId: string;
  xMm: number;
  yMm: number;
  diameterMm: number;
  lengthMm: number;
  weightKg: number;
}

export interface RebarResult {
  stirrups: DiscretizedStirrupNode[];
  longBars: DiscretizedLongBarNode[];
  mapping: RebarCageMapping;
  totalSteelWeightKg: number;
  anchorageLengthMm: number;
  longitudinalWeightKg: number;
  stirrupWeightKg: number;
}
