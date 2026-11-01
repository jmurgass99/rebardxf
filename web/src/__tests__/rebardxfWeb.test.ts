import assert from "node:assert/strict";
import { solveRebarCageWasm } from "../solver/wasmSolver.ts";

const resCoarse = await solveRebarCageWasm(450, 450, 3200, 20, 150, 250);
const resDense = await solveRebarCageWasm(450, 450, 3200, 20, 75, 150);

assert.equal(resDense.longBars.length, 8);
assert.ok(resDense.stirrups.length > resCoarse.stirrups.length);
assert.ok(resDense.anchorageLengthMm > 500);
assert.ok(resDense.totalSteelWeightKg > 80);
console.log(
  `RebarDXF WASM test OK: Long=${resDense.longBars.length} bars, Stirrups=${resDense.stirrups.length}, W_total=${resDense.totalSteelWeightKg.toFixed(1)} kg, l_b=${resDense.anchorageLengthMm.toFixed(0)} mm`
);
