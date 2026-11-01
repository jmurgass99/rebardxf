import type { RebarResult, SemanticRebarZone } from "../data-model.ts";
import { getRebarCageMesh } from "../mesh/getMesh.ts";

// Binario WebAssembly compilado desde rebarKernel.cpp
const WASM_B64 =
  "AGFzbQEAAAABDQJgAXwBfGADfHx8AXwDAwIAAQUDAQABByICCmJhckFyZWFNbTIAABFhbmNob3JhZ2VMZW5ndGhNbQABCigCEQBEGC1EVPsh6T8gAKIgAKILFAAgAEQAAAAAAADQP6IgAaIgAqML";

function decodeBase64(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") {
    return new Uint8Array(Buffer.from(b64, "base64"));
  }
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export interface RebarWasmExports {
  barAreaMm2: (dbMm: number) => number;
  anchorageLengthMm: (dbMm: number, fydMpa: number, fbdMpa: number) => number;
}

let cachedExports: RebarWasmExports | null = null;

export async function initRebarWasm(): Promise<RebarWasmExports> {
  if (cachedExports) return cachedExports;
  const { instance } = await WebAssembly.instantiate(decodeBase64(WASM_B64));
  cachedExports = instance.exports as unknown as RebarWasmExports;
  return cachedExports;
}

export async function solveRebarCageWasm(
  bMm: number,
  hMm: number,
  heightHColMm: number,
  longBarDiaMm: number,
  stirrupSpacingConfMm: number,
  stirrupSpacingMidMm: number
): Promise<RebarResult> {
  const wasm = await initRebarWasm();

  const lConf = Math.max(450, heightHColMm / 6);
  const zones: SemanticRebarZone[] = [
    {
      id: "CONF_BASE",
      zStartMm: 0,
      zEndMm: lConf,
      stirrupSpacingMm: stirrupSpacingConfMm,
      stirrupDiameterMm: 10,
    },
    {
      id: "MID_SPAN",
      zStartMm: lConf,
      zEndMm: heightHColMm - lConf,
      stirrupSpacingMm: stirrupSpacingMidMm,
      stirrupDiameterMm: 10,
    },
    {
      id: "CONF_TOP",
      zStartMm: heightHColMm - lConf,
      zEndMm: heightHColMm,
      stirrupSpacingMm: stirrupSpacingConfMm,
      stirrupDiameterMm: 10,
    },
  ];

  const { stirrups, longBars, mapping } = getRebarCageMesh(
    bMm,
    hMm,
    heightHColMm,
    40,
    longBarDiaMm,
    zones
  );

  const fyd = 435.0; // B500S o Grado 60
  const fbd = 2.7; // f_bd según EC2 / ACI 318
  const anchorageLengthMm = wasm.anchorageLengthMm(longBarDiaMm, fyd, fbd);

  const longitudinalWeightKg = longBars.reduce((acc, b) => acc + b.weightKg, 0);
  const stirrupWeightKg = stirrups.reduce((acc, s) => acc + s.weightKg, 0);
  const totalSteelWeightKg = longitudinalWeightKg + stirrupWeightKg;

  return {
    stirrups,
    longBars,
    mapping,
    totalSteelWeightKg,
    anchorageLengthMm,
    longitudinalWeightKg,
    stirrupWeightKg,
  };
}
