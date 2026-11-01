import van from "vanjs-core";
import { solveRebarCageWasm } from "./solver/wasmSolver.ts";
import { fetchRebardxfHealthApi } from "./solver/apiClient.ts";
import { createRebarViewer3D } from "./viewer/getViewer3D.ts";
import { renderCrossSectionChart, renderWeightScheduleChart } from "./ui/getRebarCharts.ts";

const { div, h2, h3, label, input, span, strong, canvas, button } = van.tags;

const colBMm = van.state(450);
const colHMm = van.state(450);
const colHeightMm = van.state(3200);
const barDiaMm = van.state(20);
const stirrupConfMm = van.state(100);

const totalWeightText = van.state("0.0 kg");
const anchorText = van.state("0 mm");
const stirrupCountText = van.state("0");
const longWeightText = van.state("0.0 kg");
const apiStatus = van.state("Modo WASM local");

const viewerWrap = div({ class: "viewer-wrap" });
const sectCanvas = canvas({ class: "chart" });
const schedCanvas = canvas({ class: "chart" });
const viewer = createRebarViewer3D(viewerWrap);

async function recompute() {
  const res = await solveRebarCageWasm(
    colBMm.val,
    colHMm.val,
    colHeightMm.val,
    barDiaMm.val,
    stirrupConfMm.val,
    200
  );
  totalWeightText.val = `${res.totalSteelWeightKg.toFixed(1)} kg`;
  anchorText.val = `${res.anchorageLengthMm.toFixed(0)} mm`;
  stirrupCountText.val = `${res.stirrups.length}`;
  longWeightText.val = `${res.longitudinalWeightKg.toFixed(1)} kg`;
  viewer.update(colBMm.val, colHMm.val, colHeightMm.val, res);
  renderCrossSectionChart(sectCanvas, colBMm.val, colHMm.val, res);
  renderWeightScheduleChart(schedCanvas, res);
}

van.derive(() => {
  void recompute();
});

const app = div(
  { class: "layout" },
  div(
    { class: "panel" },
    h2("RebarDXF 3D"),
    div(
      { class: "control-row" },
      label(() => `Sección B x H = ${colBMm.val} x ${colHMm.val} mm`),
      input({
        type: "range",
        min: "300",
        max: "800",
        step: "50",
        value: colBMm,
        oninput: (e: Event) => {
          colBMm.val = Number((e.target as HTMLInputElement).value);
          colHMm.val = colBMm.val;
        },
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Altura de columna H = ${(colHeightMm.val / 1000).toFixed(2)} m`),
      input({
        type: "range",
        min: "2400",
        max: "5000",
        step: "200",
        value: colHeightMm,
        oninput: (e: Event) => (colHeightMm.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Diámetro barra longitudinal ∅ = ${barDiaMm.val} mm`),
      input({
        type: "range",
        min: "16",
        max: "32",
        step: "4",
        value: barDiaMm,
        oninput: (e: Event) => (barDiaMm.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Espaciado cercos confinamiento (RebarCageMapping) = ${stirrupConfMm.val} mm`),
      input({
        type: "range",
        min: "50",
        max: "150",
        step: "25",
        value: stirrupConfMm,
        oninput: (e: Event) => (stirrupConfMm.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "kpi-grid" },
      div({ class: "kpi" }, span("Peso total acero"), strong(totalWeightText)),
      div({ class: "kpi" }, span("Longitud anclaje l_b"), strong(anchorText)),
      div({ class: "kpi" }, span("Total de cercos"), strong(stirrupCountText)),
      div({ class: "kpi" }, span("Peso longitudinal"), strong(longWeightText))
    ),
    button(
      {
        onclick: async () => {
          const ok = await fetchRebardxfHealthApi("http://localhost:8000");
          apiStatus.val = ok ? "FastAPI sincronizado OK" : "FastAPI offline (usando WASM local)";
        },
      },
      "Sincronizar con FastAPI"
    ),
    span({ style: "font-size:0.75rem;color:#94a3b8" }, apiStatus)
  ),
  viewerWrap,
  div(
    { class: "panel" },
    h3("Detalle de Sección Transversal"),
    sectCanvas,
    h3("Planilla de Despiece y Pesos"),
    schedCanvas
  )
);

document.getElementById("app")?.appendChild(app);
