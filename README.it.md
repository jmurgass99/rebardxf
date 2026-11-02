# rebardxf — tavole di calcestruzzo armato e distinte delle armature in DXF con ezdxf

[Español](README.md) · [English](README.en.md) · [Português](README.pt.md) · **Italiano**

Sezioni di travi, pilastri e pareti con la loro armatura, tavole di dettaglio di pilastri e plinti con distinta e cartiglio, pianta delle fondazioni che ricava la disposizione dei ferri da A_s e dichiara lo stato di calcolo, prospetti di telaio con conteggio esatto delle entità, tabella dei pilastri per piano, forme dei ferri con i diametri di piegatura della ACI 318-19 §25.3, lunghezze di taglio in asse (BS 8666), distinte e quantità, cartigli A1/A3 nello spazio carta, layer in spagnolo e AIA/ISO 13567, esportazione con versione DXF fissata, DXF per Revit Link CAD e API REST. Unica dipendenza: `ezdxf`.

[![CI](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Quale problema risolve

La tavola delle armature è dove il calcolo diventa cantiere, e dove si perde di più: l'A_s della relazione si traduce a mano in «Ø16/175», la distinta somma le quote esterne invece delle lunghezze di taglio, la tabella dei pilastri si riempie copiando, e quando manca un dato qualcuno disegna un'armatura «tipo» che si legge come calcolata. `rebardxf` genera quelle tavole da Python con le regole in vista: la disposizione deriva da A_s con i limiti di interasse ACI o EC2 e resta scritta nel DXF, nella tabella e nell'etichetta con lo stesso numero; le lunghezze di taglio detraggono le pieghe; ogni generatore dichiara quante entità disegna e i test lo verificano rileggendo il file; e un dato mancante produce NO_CALCULADO nella tavola, mai un ferro inventato. I file si aprono in AutoCAD, BricsCAD, LibreCAD, Revit (Link CAD) o in qualsiasi visualizzatore DXF.

**Usalo quando**

- hai il risultato di un dimensionamento (b, h, ferri, staffe, A_s al metro) e vuoi la sezione, la tavola di dettaglio o la pianta in DXF senza passare dal disegnatore a ogni iterazione;
- ti servono distinte con lunghezze di taglio in asse, pesi per posizione e per diametro, quantità per elemento e forme dei ferri con i D minimi della ACI 318-19;
- vuoi una tabella dei pilastri per piano, un prospetto schematico di telaio con le staffe o una tavola A1/A3 con cartiglio nello spazio carta e finestra in scala;
- generi DXF per altri programmi: versione R2010 fissata per Revit o per le piegatrici, layer AIA, stile SHX, o un'API REST che restituisce il DXF in base64.

**Non usarlo per**

- dimensionare: il pacchetto non calcola A_s, ancoraggi né sovrapposizioni; disegna e distribuisce ciò che riceve e verifica interassi e percentuali minime;
- tavole esecutive complete con dettagli costruttivi (nodi, riprese, giunti): sono generatori di elementi e tabelle, non un BIM;
- sezioni con diametri misti in uno strato (`BeamDetail` disegna ogni strato con il primo Ø; usa il collegamento `RCSectionDesign` ferro per ferro), pilastri circolari o staffe multiple;
- sostituire la revisione della tavola: lo stato REQUIERE_REVISION esiste proprio perché qualcuno guardi.

## Installazione

```bash
pip install git+https://github.com/jmurgass99/rebardxf.git
```

Extra: `api` (FastAPI, pydantic, httpx), `autocad` (invio in tempo reale con pyautocad, solo Windows), `test`. Per lo sviluppo: `git clone`, `pip install -e ".[test,api]"`, `pytest -q` (30 file di test; `tests/test_examples.py` esegue i 25 esempi come sottoprocessi). Su Windows, se la console non è UTF-8, esegui gli esempi con `python -X utf8 examples/<nome>.py`. Gli esempi scrivono i loro DXF in `examples/out/` (non versionato) e il loro output di console in `examples/output/`.

## Funzionalità

| Funzionalità | Moduli | Norma o riferimento | Casi d'uso |
|---|---|---|---|
| Sezioni e dettagli degli elementi: trave (due strati, A_s, retino, staffa), pilastro (disposizione perimetrale da 4 a 16+ ferri, ρ), parete con elementi di bordo e due reti (ρ_v, ρ_h, ρ_be rispetto ai minimi), tavola di dettaglio del pilastro (prospetto, tre sezioni, distinta, cartiglio) e del plinto (pianta, sezione, distinta) | `beam_section`, `column_section`, `wall_detail`, `column_rebar_detail`, `footing_rebar_detail`, `services` | ACI 318 §11.6 (percentuali delle pareti); ISO 3766 (rappresentazione) | [5 casi](#1-sezioni-e-dettagli-degli-elementi) |
| Pianta delle fondazioni e prospetti: disposizione dei ferri da A_s con s_min/s_max della ACI 318-19 (§25.2.1, §13.3.2.1) o della EN 1992-1-1 (§8.2, §9.3.1.1), stato per plinto (CALCULADO_CUMPLE / REQUIERE_REVISION / NO_CALCULADO) scritto in tavola e in tabella, servizio con dizionari JSON; prospetto di telaio con assi, livelli, armature e staffe nelle zone critiche e conteggio chiuso delle entità | `foundation_plan`, `frame_elevation`, `services.footing_drawings` | ACI 318-19 §25.2.1, §13.3.2.1, §18.6.4, §18.7.5; EN 1992-1-1 §8.2, §9.3.1.1; EN 1997-1 (copriferro contro terra) | [5 casi](#2-pianta-delle-fondazioni-e-prospetti) |
| Distinta delle armature: forme dei ferri (uncini a 90/135/180, staffe chiuse e aperte, L, U, S) con il D minimo della ACI 318-19 §25.3 per designazione #/M/mm, lunghezza di taglio in asse e detrazione dalle quote esterne, distinta con pesi per posizione e diametro, quantità in kg/m³ con designazioni di USA, UE, AU e CO, tabella degli acciai e delle revisioni come geometria | `rebar_shapes`, `rebar_cut_length`, `rebar_schedule`, `rebar_quantities`, `rebar_schedule_block`, `revision_block` | ACI 318-19 §25.3; ACI Detailing Manual; BS 8666; ISO 3766; ASTM A615 | [5 casi](#3-distinta-delle-armature-forme-lunghezze-di-taglio-e-quantità) |
| Tabelle, tavole, layer e scale: tabella dei pilastri piani × pilastri con la sezione in scala e statistiche esatte, tavola A4–A0 con cornice, cartiglio e finestra nello spazio carta, modelli costruttivi come geometria senza ezdxf, registro dei layer con colore/tipo di linea/spessore, 21 layer AIA, cinque standard di nomenclatura, scale e altezze del testo | `column_schedule_grid`, `templates`, `templates_construction`, `layers`, `aia_layers`, `layer_standards`, `scales` | ISO 216; AIA CAD Layer Guidelines / NCS; ISO 13567; BCA CORENET; NATSPEC; NTC 1960 | [5 casi](#4-tabelle-tavole-layer-e-scale) |
| Esportazione, integrazioni, API e stato di calcolo: `save_dxf` con versione R2000–R2018 fissata, audit, `verify`, `clean`; collegamento da un progetto di sezione ferro per ferro; DXF per Revit Link CAD (2D, $INSUNITS, SHX); API REST con DXF in base64 o come file e 422; contratto `CalculationStatus` chiuso per default | `export`, `integration.fastsap_bridge`, `integration.revit_dxf_link`, `api`, `_common.audit_status` | Autodesk DXF Reference; Revit «Importing CAD»; FastAPI | [5 casi](#5-esportazione-integrazioni-api-e-stato-di-calcolo) |

I 25 script di `examples/` sono stati eseguiti in un ambiente pulito prima della pubblicazione; il loro output è in `examples/output/` ed è quello riprodotto qui. Ognuno rilegge il DXF generato con ezdxf e ne conta le entità.

## Casi d'uso

Gli output sono riportati esattamente come li stampano gli script, in spagnolo.

### 1. Sezioni e dettagli degli elementi

#### Sezione di trave 300 × 500 con due strati: posizioni, A_s, conteggio delle entità e il limite con diametri misti

<details><summary>Output reale di <code>python examples/beam_section_300x500_two_layers_as_summary_entity_count_and_mixed_diameter_limit.py</code></summary>

```text
Viga V-101: 300 × 500 mm, recubrimiento 30 mm, estribo Ø10
  Armado superior [(16.0, 2)] → A_s = 402.1 mm² (2·π·16²/4 = 402.1); inferior [(20.0, 3)] → A_s = 942.5 mm² (3·π·20²/4 = 942.5)
  Posiciones x de las 3 barras inferiores (ancho útil b − 2·(c + Ø_e + Ø/2) = 200 mm): [50, 150, 250] mm; cota y = c + Ø_e + Ø/2 = 50 mm
  Cuantía ρ = A_s,inf/(b·d) con d = h − c − Ø_e − Ø/2 = 450 mm → 0.70 %

DXF V-101_section.dxf: contador interno {'lines': 8, 'circles': 5, 'texts': 2, 'rects': 2}; releído con ezdxf {'LINE': 8, 'HATCH': 1, 'CIRCLE': 5, 'TEXT': 2}; verify → {'ok': True, 'errors': 0, 'fixes': 0, 'dxfversion': 'AC1032', 'n_modelspace_entities': 16}
  Capas presentes: ['ARMADURA', 'CONCRETO', 'ESTRIBO', 'RELLENO', 'TEXTO']
  Textos: ['V-101', 'As,top=402 mm²  As,bot=942 mm²']

Viga V-102 con capa inferior 2Ø20 + 1Ø16: A_s,inf = 829.4 mm² (correcto), pero los radios dibujados son [8.0, 10.0] mm: las tres barras inferiores salen con Ø20 porque el dibujo usa el primer diámetro de cada capa. Para mezclar diámetros en el plano, usa `integration.fastsap_bridge.RCSectionDesign` (barra a barra).
```

</details>

#### Sezione di pilastro con da 4 a 16 ferri: disposizione perimetrale, ρ e il difetto corretto che sovrapponeva i ferri in 12Ø20

<details><summary>Output reale di <code>python examples/column_section_bar_layouts_4_to_16_bars_perimeter_distribution_rho_and_fixed_overlap.py</code></summary>

```text
Pilar 500 × 500 mm, recubrimiento 40 mm, estribo Ø10, barras Ø20:
  barras posiciones distintas por cara horiz. por cara vert. A_s [mm²]  ρ [%]
       4          4         4               2              2      1257   0.50
       6          6         6               2              3      1885   0.75
       8          8         8               2              4      2513   1.01
      10         10        10               2              5      3142   1.26
      12         12        12               3              5      3770   1.51
      14         14        14               4              5      4398   1.76
      16         16        16               4              6      5027   2.01

DXF C-12_section.dxf: {'LINE': 8, 'HATCH': 1, 'CIRCLE': 12, 'TEXT': 3, 'DIMENSION': 1} → 12 círculos para 12 barras (hasta la 1.2.0 salían 10, con dos pares superpuestos en una esquina)
  Rótulos: ['C-12', '12Ø20  ρ=1.51%', 'fc=30.0 MPa  fy=500.0 MPa']

Pilar 300 × 600 con 10Ø25: 2 barras en cada cara corta y 5 en cada cara larga (10 posiciones distintas); ρ = 2.73 %; resumen: 10 barras, Ø máx 25, A_g = 18 cm²
Caso impar 9Ø20: 9 posiciones, 8 distintas: no hay reparto perimetral simétrico y la última se repite (documentado en el docstring).

Las esquinas van siempre armadas y el resto se reparte por caras; con diámetros mezclados en `bars` se dibuja el mayor. Para pilares circulares o con dos estribos hace falta otro generador.
```

</details>

#### Sezione di parete di 4 m con elementi di bordo e due reti: percentuali rispetto ai minimi della ACI 318 §11.6

<details><summary>Output reale di <code>python examples/wall_section_boundary_elements_web_curtains_and_minimum_ratios_aci_318_11_6.py</code></summary>

```text
Muro M-1: L_w = 4000, t_w = 250, L_be = 600 mm; borde 8Ø20; alma Ø12 c/200 en dos cortinas
  ρ_be = 8·π·20²/4/(250·600) = 1.68 % (paquete 1.676, mínimo 1 %) → cumple
  ρ_v = 2·(π·12²/4)·(1000/200)/(250·1000) = 0.452 % (paquete 0.452, mínimo 0.25 %) → cumple; ρ_h = 0.452 % → cumple

DXF M-1_section.dxf: {'LINE': 22, 'HATCH': 1, 'CIRCLE': 44, 'TEXT': 4, 'DIMENSION': 2}; círculos = 2 bordes × 8 + 2 cortinas × 14 puntos de alma = 44; contador interno {'lines': 22, 'circles': 44, 'texts': 4, 'rects': 5}

Barrido de la separación del alma (Ø12, dos cortinas, t_w = 250):
  s [mm] ρ_v [%]  mínimo  veredicto
     150   0.603    0.25  cumple
     200   0.452    0.25  cumple
     250   0.362    0.25  cumple
     300   0.302    0.25  cumple
     350   0.259    0.25  cumple

Servicio draw_wall_section M-2 (6 m × 0,3 m, borde 10Ø25, alma Ø12 c/150): 109 entidades; ρ_be = 2.04 %, ρ_v = 0.503 %
  Bordes que no caben (2·600 ≥ 1000) → GeometryError: Los elementos de borde no caben en el muro

Con Ø12 en dos cortinas y t_w = 250 el 0,25 % de ACI 318 §11.6.2 se cumple hasta s ≈ 360 mm; la norma limita además s ≤ mín(l_w/5, 3·t_w, 450 mm) y EC8 §5.4.3.5 pide 0,2–0,3 % según la zona: el paquete solo comprueba la cuantía y rotula los valores para que el revisor los vea en el plano. El elemento de borde no se dimensiona aquí (longitud y confinamiento son datos).
```

</details>

#### Tavola di dettaglio di un pilastro: prospetto, tre sezioni, distinta con pesi e cartiglio

<details><summary>Output reale di <code>python examples/column_rebar_detail_sheet_elevation_three_sections_schedule_weights_and_titleblock.py</code></summary>

```text
Pilar C-7 500 × 500 mm, H = 3600 mm, recubrimiento 40 mm
  marca   Ø  L [m]   n forma    kg/m peso [kg]
     L1  20   4.20   8    L1   2.466      82.9
     L2  16   1.20   4    L1   1.578       7.6
     E1  10   1.84  26    51   0.617      29.5
     E2  10   1.84   6    51   0.617       6.8
  TOTAL = 126.7 kg; comprobación L1: 7850·π·0,02²/4·4,20·8 = 82.9 kg; Ø10 pesa 0.617 kg/m (tabla 0,617)

DXF C-7_despiece.dxf: {'LWPOLYLINE': 33, 'LINE': 2, 'TEXT': 39, 'CIRCLE': 36}; por capa {'CONCRETO': 4, 'ARMADURA': 38, 'TEXTO': 63, 'COTAS': 1, 'ESTRIBO': 3, 'CAJETIN': 1}
  Textos de cabecera y planilla: ['ALZADO C-7', 'PLANILLA DE ARMADURA', 'TOTAL = 126.7 kg', 'Proyecto: Edificio de oficinas — Bloque B', 'Elemento: C-7']
  Secciones: ['BASE', 'MEDIA', 'CABEZA']; círculos dibujados = 36 = 3 secciones × 12 por sección; barras reales = 12 → todas dibujadas en cada corte

Servicio draw_column_rebar C-8: total 173.65 kg, 1 marcas longitudinales, 1 de estribo → C-8_despiece.dxf

La planilla y el cajetín salen en el mismo espacio modelo que el alzado (unidades mm); para una lámina con cajetín en espacio papel se usa `SheetTemplate.apply_to_layout` sobre este documento.
```

</details>

#### Dettaglio di un plinto di 2,4 × 2,4 × 0,6 m con rete inferiore e armatura superiore: pianta, sezione e distinta

<details><summary>Output reale di <code>python examples/footing_rebar_detail_plan_section_schedule_two_way_mats_z1_and_service.py</code></summary>

```text
Zapata Z-1 2400 × 2400 × 600 mm, recubrimiento 50 mm; A_s requerido 1150 mm²/m por dirección
  Ø16: A_b = 201.1 mm² → s_req = 175 mm → 15 barras a 164 mm (A_s real 1224 mm²/m); longitud de corte con patillas 12Ø: 2.68 m
  Pesos: inferior X 63.5 kg, inferior Y 63.5 kg, superior X 16.3, superior Y 16.3 → total 159.8 kg; cuantía 46.2 kg/m³ de hormigón

DXF Z-1_despiece.dxf: {'LWPOLYLINE': 33, 'LINE': 30, 'TEXT': 34, 'CIRCLE': 23}; planta con 15 + 15 líneas de parrilla, sección con 15 + 8 círculos (inferior y superior)
  Títulos: ['VISTA EN PLANTA', 'SECCION A-A', 'PLANILLA ZAPATA Z-1', 'TOTAL = 159.8 kg']; filas de planilla: ['BOT-X', 'BOT-Y', 'TOP-X', 'TOP-Y']

Servicio draw_footing_rebar Z-2 (3,0 × 2,0 × 0,7, Ø20 c/≈240 en X y Ø16 c/≈120 en Y): 172.22 kg → Z-2_despiece.dxf
  Sin ninguna posición de armadura → ConfigurationError: Debe especificar al menos una posicion de armadura

El detalle dibuja lo que se le da (número de barras, longitudes): el reparto a partir de A_s y las longitudes de anclaje son del calculista, aquí hechos a mano; `FoundationPlan` sí deriva el reparto desde A_s con los límites de separación de ACI/EC2.
```

</details>

### 2. Pianta delle fondazioni e prospetti

#### Pianta con sei plinti: dall'A_s richiesto alla disposizione disegnata con i limiti di interasse della ACI 318-19 e della EN 1992-1-1

<details><summary>Output reale di <code>python examples/foundation_plan_six_footings_rebar_layout_from_as_required_aci_vs_ec2_spacing_limits.py</code></summary>

```text
layout_rebar_direction para una zapata de B = 2,4 m y h = 0,6 m (recubrimiento 75 mm, árido 20 mm):
  A_s [mm²/m]   Ø     norma s_req [mm] s_mín s_máx   n s dibujada rótulo  estado
          600  12 ACI318-19        188    39   450  13      187.5    188  CALCULADO_CUMPLE
          600  12       EC2        188    37   400  13      187.5    188  CALCULADO_CUMPLE
          600  16 ACI318-19        335    43   450   8      321.4    321  CALCULADO_CUMPLE
          600  16       EC2        335    41   400   8      321.4    321  CALCULADO_CUMPLE
          600  25 ACI318-19        818    52   450   0      818.1    450  REQUIERE_REVISION — s_req (818mm) > s_max (450mm) — aumentar db
          600  25       EC2        818    50   400   0      818.1    400  REQUIERE_REVISION — s_req (818mm) > s_max (400mm) — aumentar db
         1150  12 ACI318-19         98    39   450  24       97.8     98  CALCULADO_CUMPLE
         1150  12       EC2         98    37   400  24       97.8     98  CALCULADO_CUMPLE
         1150  16 ACI318-19        175    43   450  14      173.1    173  CALCULADO_CUMPLE
         1150  16       EC2        175    41   400  14      173.1    173  CALCULADO_CUMPLE
         1150  25 ACI318-19        427    52   450   7      375.0    375  CALCULADO_CUMPLE
         1150  25       EC2        427    50   400   0      426.8    400  REQUIERE_REVISION — s_req (427mm) > s_max (400mm) — aumentar db
         2400  12 ACI318-19         47    39   450  49       46.9     47  CALCULADO_CUMPLE
         2400  12       EC2         47    37   400  49       46.9     47  CALCULADO_CUMPLE
         2400  16 ACI318-19         84    43   450  28       83.3     83  CALCULADO_CUMPLE
         2400  16       EC2         84    41   400  28       83.3     83  CALCULADO_CUMPLE
         2400  25 ACI318-19        205    52   450  13      187.5    188  CALCULADO_CUMPLE
         2400  25       EC2        205    50   400  13      187.5    188  CALCULADO_CUMPLE

Cuadro de zapatas (schedule_table):
  zapata      B × L × h [m] A_s,x / A_s,y   Ø     norma            estado  rótulo del plano
     Z-1    2.4 × 2.4 × 0.6   1150 / 1150  16 ACI318-19  CALCULADO_CUMPLE  Ø16 c/173+Ø16 c/173
     Z-2    2.8 × 2.8 × 0.7   1400 / 1400  16 ACI318-19  CALCULADO_CUMPLE  Ø16 c/139+Ø16 c/139
     Z-3    2.0 × 2.0 × 0.5     800 / 800  12 ACI318-19  CALCULADO_CUMPLE  Ø12 c/132+Ø12 c/132
     Z-4    2.4 × 3.0 × 0.6   1150 / 1500  16       EC2  CALCULADO_CUMPLE  Ø16 c/173+Ø16 c/130
     Z-5    3.2 × 3.2 × 0.8   1900 / 1900  20       EC2  CALCULADO_CUMPLE  Ø20 c/161+Ø20 c/161
     Z-6    2.0 × 2.0 × 0.5     800 / 800  12       EC2  CALCULADO_CUMPLE  Ø12 c/132+Ø12 c/132

DXF planta_cimentacion.dxf: {'LINE': 265, 'HATCH': 6, 'TEXT': 18, 'DIMENSION': 6}; contador interno {'lines': 265, 'circles': 0, 'texts': 18, 'rects': 12}; capas: ['ARMADURA', 'CONCRETO', 'COTAS', 'EJES', 'RELLENO', 'TEXTO']

El mismo A_s con Ø mayor da menos barras pero puede chocar con s_máx (Ø25 con 600 mm²/m pide 818 mm > 450): el paquete lo marca REQUIERE_REVISION en vez de recortar la separación en silencio. El parámetro `s_commercial_step_mm` se acepta pero el rótulo redondea al milímetro: el redondeo a múltiplos de 25 mm queda para el delineante.
```

</details>

#### Dati incompleti o impossibili: NO_CALCULADO, REQUIERE_REVISION e la regola di non inventare armature nella tavola

<details><summary>Output reale di <code>python examples/foundation_plan_status_no_calculado_requiere_revision_never_fabricates_rebar.py</code></summary>

```text
Estado al construir FootingData (antes de dibujar):
  Z-OK       status = NO_CALCULADO      notas = «»
  Z-SIN-AS   status = NO_CALCULADO      notas = «NO CALCULADO — ARMADO NO DEFINIDO»
  Z-SIN-DB   status = REQUIERE_REVISION notas = «As=1150/1150 mm2/m — Ø NO DEFINIDO»
  Z-CONGEST  status = NO_CALCULADO      notas = «»
  Z-S-MAX    status = NO_CALCULADO      notas = «»

Cuadro tras dibujar (schedule_table) y rótulo estampado en el plano:
  Z-OK       CALCULADO_CUMPLE  A_s = 1150.0 / 1150.0, Ø = 16.0  → «Ø16 c/173+Ø16 c/173»
  Z-SIN-AS   NO_CALCULADO      A_s = None / None, Ø = None  → «NO CALCULADO — ARMADO NO DEFINIDO»
             motivo: NO CALCULADO — ARMADO NO DEFINIDO
  Z-SIN-DB   REQUIERE_REVISION A_s = 1150.0 / 1150.0, Ø = None  → «REQUIERE REVISION — As=1150/1150 mm2/m — Ø NO DEFINIDO»
             motivo: As=1150/1150 mm2/m — Ø NO DEFINIDO
  Z-CONGEST  REQUIERE_REVISION A_s = 4500.0 / 4500.0, Ø = 12.0  → «REQUIERE REVISION — s_req (25mm) < s_min (37mm) — congestión de armadura; s_req (25mm) < s_min (37mm) — congestión de armadura»
             motivo: s_req (25mm) < s_min (37mm) — congestión de armadura; s_req (25mm) < s_min (37mm) — congestión de armadura
  Z-S-MAX    REQUIERE_REVISION A_s = 400.0 / 400.0, Ø = 25.0  → «REQUIERE REVISION — s_req (1227mm) > s_max (450mm) — aumentar db; s_req (1227mm) > s_max (450mm) — aumentar db»
             motivo: s_req (1227mm) > s_max (450mm) — aumentar db; s_req (1227mm) > s_max (450mm) — aumentar db

Líneas en la capa ARMADURA: 28 = 14 + 14 de la única zapata calculada (Ø16 c/173); las otras cuatro no aportan ninguna.
Entidades del DXF: {'LINE': 78, 'HATCH': 5, 'TEXT': 15, 'DIMENSION': 5}

Agregado de los cinco estados: CALCULADO_CUMPLE + 4 no favorables → el plano no puede firmarse; `aggregate_calculation_statuses` da NO_CALCULADO.
La ausencia se propaga como ausencia: un dato que falta produce NO_CALCULADO con la lista de lo que falta, nunca un armado por defecto que se lea como aprobado.
```

</details>

#### Servizio `draw_footing_plan`: input in dizionari, tabella serializzabile e validazione dei campi

<details><summary>Output reale di <code>python examples/foundation_plan_service_metadata_schedule_and_json_ready_output_for_rest_clients.py</code></summary>

```text
draw_footing_plan → planta_servicio.dxf: 4 zapatas, 163 entidades internas {'lines': 143, 'circles': 0, 'texts': 12, 'rects': 8}

Cuadro devuelto (listo para JSON):
  zapata      B × L × d [m]  A_s,x  A_s,y    Ø            estado  notas
    Z-A1 2.20 × 2.20 × 0.55 1000.0 1000.0 16.0  CALCULADO_CUMPLE  
    Z-A2 2.60 × 2.60 × 0.65 1300.0 1300.0 16.0  CALCULADO_CUMPLE  
    Z-B1 2.00 × 2.60 × 0.55  900.0 1200.0 12.0  CALCULADO_CUMPLE  
    Z-B2 2.60 × 2.60 × 0.65   None   None None      NO_CALCULADO  NO CALCULADO — ARMADO NO DEFINIDO

  JSON del cuadro: 656 caracteres; primera fila: [{"label": "Z-A1", "B_m": 2.2, "L_m": 2.2, "d_m": 0.55, "As_x_mm2_m": 1000.0, "As_y_mm2_m": 1000.0, "db_mm": 16.0, "stat…
  Validación (sin canto d) → ConfigurationError: Zapata sin campo obligatorio 'd'
  Validación (B negativo) → GeometryError: Dimensiones invalidas en Z-Y
  Validación (lista vacía) → ConfigurationError: Debe haber al menos una zapata

El servicio es la frontera que usa la API REST (`/api/drawings/footing`): los errores tipados se traducen a 422 y el cuadro viaja tal cual. Z-B2 sin A_s sale NO_CALCULADO en el cuadro y «ARMADO NO DEFINIDO» en el plano.
```

</details>

#### Prospetto di un telaio a 2 campate e 2 piani: il numero esatto di entità ricavato a mano e verificato nel DXF

<details><summary>Output reale di <code>python examples/frame_elevation_two_bays_two_storeys_exact_entity_count_derivation_vs_dxf.py</code></summary>

```text
Pórtico PORTICO-B (Eje B): vanos [5000.0, 6000.0] mm, pisos [3500.0, 3000.0] mm → 3 ejes, 3 niveles, 6 pilares, 4 vigas

Estribos por pieza (zona crítica + central + crítica):
  pilar piso 1: H libre 3000 mm → 2·5 + 10 = 20 estribos
  pilar piso 2: H libre 2500 mm → 2·5 + 7 = 17 estribos
  viga vano 1: L libre 4600 mm → 2·8 + 15 = 31 estribos
  viga vano 2: L libre 5600 mm → 2·8 + 20 = 36 estribos

Derivación: líneas = 3 ejes + 3 niveles + 2·6 contorno pilares + 2·4 contorno vigas + 2·6 armado pilares + 111 estribos pilar + 2·4 armado vigas + 134 estribos viga = 291
            círculos = 3 (una burbuja por eje); textos = 1 + 3 + 3 + 6 + 4 = 17; total 311

DXF alzado_portico_B.dxf releído: {'LINE': 291, 'CIRCLE': 3, 'TEXT': 17} → COINCIDE con la derivación
  Por capa: {'EJES': 9, 'TEXTO': 17, 'CONCRETO': 20, 'ARMADURA': 20, 'ESTRIBO': 245}
  Rótulos: ['A', 'B', 'C', 'N.+0.00 m', 'N.+3.50 m', 'N.+6.50 m', 'C1-P1', 'C1-P2', 'C2-P1', 'C2-P2', 'C3-P1', 'C3-P2'] …

El recuento cerrado es la prueba de regresión del generador: cualquier cambio en el reparto de estribos o en los rótulos rompe la igualdad. El alzado es esquemático (dos líneas por armado); el despiece barra a barra va en los detalles de pilar y viga.
```

</details>

#### Quante staffe porta un telaio 3 × 3 in funzione degli interassi nelle zone critiche e centrali

<details><summary>Output reale di <code>python examples/frame_elevation_stirrup_counts_critical_zones_spacing_sweep_three_storeys.py</code></summary>

```text
Pórtico 3 × 3: vanos [6000.0, 4500.0, 6000.0], pisos [4000.0, 3300.0, 3300.0], pilares 500 × 500, vigas 300 × 550 → 12 pilares y 9 vigas
Cerco de pilar Ø10 ≈ 1.20 kg, cerco de viga Ø10 ≈ 1.07 kg (perímetro al recubrimiento + 2 ganchos de 135 mm)

  s_crit s_cent l_c pilar l_c viga estribos pilar estribos viga  total peso cercos [kg] líneas DXF
      75    200       500     1100            256           375    631              708        723
      75    200       600     1100            292           375    667              751        759
     100    150       500     1100            272           366    638              717        730
     100    200       500     1100            232           321    553              621        645
     100    200       600     1100            244           321    565              636        657
     100    250       500     1100            212           297    509              572        601
     125    200       500     1100            208           267    475              535        567
     125    200       600     1100            196           267    463              520        555

Caso más denso (752 estribos, s_crit = 75, s_cent = 150, l_c = 600) dibujado en alzado_portico_3_denso.dxf: {'LINE': 844, 'CIRCLE': 4, 'TEXT': 30, 'total_entities': 878}
  Pilar del piso 1 (H libre 3450 mm): 31 estribos = 2·⌊600/75⌋ + ⌊(3450 − 2·600)/150⌋

Pasar de s_cent 250 a 150 sube el total de estribos un 25 % (509 → 638) y de s_crit 125 a 75 otro 33 %: la zona central pesa tanto como la crítica en el número de cercos aunque la crítica domine la fotografía del alzado. El recuento es de líneas dibujadas (un estribo = una línea en el alzado); la planilla real necesita las longitudes de corte de `rebar_cut_length`.
```

</details>

### 3. Distinta delle armature: forme, lunghezze di taglio e quantità

#### Catalogo delle forme: diametri minimi di piegatura della ACI 318-19 §25.3, vertici di uncini e staffe, e polilinee in DXF

<details><summary>Output reale di <code>python examples/rebar_shapes_catalog_hooks_stirrups_aci_318_25_3_bend_diameters_and_polylines_to_dxf.py</code></summary>

```text
Diámetro interior mínimo de doblado D [mm] (ACI 318-19 §25.3) y D/Ø:
   barra  Ø [mm] gancho 90/180 cerco 90/135  sísmico
      #3    9.53    57.2 (6Ø)    38.1 (4Ø)     57.2   (tabla como #3)
      #4   12.70    76.2 (6Ø)    50.8 (4Ø)     76.2   (tabla como #4)
      #5   15.88    95.2 (6Ø)    63.5 (4Ø)     95.2   (tabla como #5)
      #6   19.05   114.3 (6Ø)   114.3 (6Ø)    114.3   (tabla como #6)
      #8   25.40   152.4 (6Ø)   152.4 (6Ø)    152.4   (tabla como #8)
      #9   28.65   229.2 (8Ø)  no tabulado    229.2   (tabla como #9)
     #11   35.81   286.5 (8Ø)  no tabulado    286.5   (tabla como #11)
     #14   43.00   430.0 (10Ø)  no tabulado        —   (tabla como #14)
     M10   10.00    60.0 (6Ø)    40.0 (4Ø)     60.0   (tabla como #3)
     M16   16.00    96.0 (6Ø)    64.0 (4Ø)     96.0   (tabla como #5)
     M25   25.00   150.0 (6Ø)   150.0 (6Ø)    150.0   (tabla como #8)
      12   12.00    72.0 (6Ø)    48.0 (4Ø)     72.0   (tabla como #4)
      32   32.00   256.0 (8Ø)  no tabulado    256.0   (tabla como #10)
  Extensión de la cola: 90° máx(12Ø, 150) = 192 mm para Ø16; 135° máx(6Ø, 75) = 75 para Ø10; 180° máx(4Ø, 65) = 80 para Ø20

  forma                                  vértices ancho × alto caja [mm] radio interior usado
  hook_90 Ø16 pierna 600 (ACI)                 12              600 × 192              48.0 mm
  hook_90 Ø16 pierna 600 (legacy 3Ø)           12              600 × 192              48.0 mm
  hook_135 Ø10 pierna 300                      12               347 × 87                     
  closed_stirrup 300×500 c30 Ø10               43              230 × 430                     
  open_stirrup 300×500 c30 Ø10                 24              230 × 430                     
  L_shape 1000+500 Ø16                         12             1000 × 500              48.0 mm
  U_shape ancho 240 patas 400 Ø12              22              240 × 400                     
  S_shape 300/60/300 Ø12                        4               60 × 630                     

DXF formas_barra.dxf: {'LWPOLYLINE': 8, 'TEXT': 8} (8 polilíneas, una por forma, en la capa ARMADURA)
Catálogo por nombre: [True, True, True, True, True, True, True, True]; p. ej. ShapeCatalog.get('hook90')(leg=500, db=16) → 12 vértices

Con `bar=` el radio sale de la tabla ACI (Ø16 cerco: 4Ø → r = 32 mm; gancho estándar 6Ø → 48 mm); sin él la aproximación heredada da 3Ø. Las formas L, U y S aún no aceptan `bar=` y usan siempre la heredada: para una planilla normativa pásalas por `rebar_cut_length` con el D de la tabla.
```

</details>

#### Lunghezza di taglio in asse contro quote esterne: detrazione per piega nei ferri a L, a U e nelle staffe (BS 8666)

<details><summary>Output reale di <code>python examples/rebar_cut_length_centerline_vs_out_to_out_bend_deductions_l_u_stirrup_bs8666.py</code></summary>

```text
Arco por la fibra neutra y deducción out-to-out por doblez [mm]:
    Ø D cerco arco 90° ded. 90° arco 135° ded. 135° | D gancho arco 90° ded. 90° arco 180°
    8    32.0     31.4     16.6      47.1      68.8 |     48.0     44.0     20.0      88.0
   10    40.0     39.3     20.7      58.9      85.9 |     60.0     55.0     25.0     110.0
   12    48.0     47.1     24.9      70.7     103.1 |     72.0     66.0     30.0     131.9
   16    64.0     62.8     33.2      94.2     137.5 |     96.0     88.0     40.0     175.9
   20   120.0    110.0     50.0     164.9     221.3 |    120.0    110.0     50.0     219.9
   25   150.0    137.4     62.6     206.2     276.7 |    150.0    137.4     62.6     274.9
  La deducción a 90° crece con Ø y con D: para Ø16 de gancho (D = 96) son 40 mm por esquina, el error clásico de la planilla que suma cotas exteriores.

Barra en L (código 11) Ø16, cotas exteriores 1200 + 400, D = 96 mm (r = 48):
  tramos rectos al eje 1136 + 336 + arco 88.0 = 1560.0 mm; desde cotas exteriores 1600 − 40.0 = 1560.0 mm → coinciden; suma ingenua de cotas: 1600 (+40 mm de más)

Barra en U (código 21) Ø12, cotas 450 + 240 + 450, D = 72: longitud de corte 1079.9 mm = 1140 − 2·30.0

Cerco cerrado (código 51) 240 × 440 exteriores (sección 300 × 500, c = 30), Ø10, D = 40 mm, colas de 135° = 75 mm:
  4 tramos rectos al eje [180, 380, 180, 380] + 3 arcos de 90° + 2 arcos de 135° + 2 colas = 1506 mm; perímetro exterior 1360 + 2 colas = 1510 (la planilla rápida); diferencia +4 mm
  Peso por cerco Ø10: 0.928 kg; en una viga con 60 cercos la planilla rápida pide 0.3 m de más.

Medir por la fibra neutra o restar la deducción es lo mismo; sumar cotas exteriores no. Con D pequeño (cercos Ø10, D = 40) la diferencia son milímetros por pieza; con Ø25 y D = 150 son 6 cm por doblez, 12 cm en una barra en U.
```

</details>

#### Distinta di una trave di 6 m: posizioni, pesi per diametro, conservazione della massa e il servizio

<details><summary>Output reale di <code>python examples/rebar_schedule_beam_marks_weights_by_diameter_mass_conservation_and_service.py</code></summary>

```text
Planilla V-101 (longitudes de corte en mm):
 Mark  Element   db    n    L(mm)  Total(kg)
--------------------------------------------
    1    V-101   20    3     6350     46.980
    2    V-101   16    2     6350     20.045
    3    V-101   16    2     2400      7.576
    4    V-101   10   42     1544     39.981
    5    V-101    8   12      540      2.557
============================================
                                   TOTAL     117.14 kg

Filas de to_table():
  marca 1 straight Ø20 n =   3 L =   6350 mm ΣL =  19.05 m × 2.4662 kg/m =  46.980 kg
  marca 2 straight Ø16 n =   2 L =   6350 mm ΣL =  12.70 m × 1.5783 kg/m =  20.045 kg
  marca 3 straight Ø16 n =   2 L =   2400 mm ΣL =   4.80 m × 1.5783 kg/m =   7.576 kg
  marca 4  stirrup Ø10 n =  42 L =   1544 mm ΣL =  64.85 m × 0.6165 kg/m =  39.981 kg
  marca 5        U Ø8  n =  12 L =    540 mm ΣL =   6.48 m × 0.3946 kg/m =   2.557 kg

Por diámetro: {8: {'total_kg': 2.56}, 10: {'total_kg': 39.98}, 16: {'total_kg': 27.62}, 20: {'total_kg': 46.98}}; suma = 117.14 kg frente a total_weight = 117.14 kg → conservación OK
kg/m exacto frente a la regla 0,006165·Ø²:
  Ø 8: 0.3946 kg/m, regla 0.3946, tabla comercial 0.395
  Ø10: 0.6165 kg/m, regla 0.6165, tabla comercial 0.617
  Ø12: 0.8878 kg/m, regla 0.8878, tabla comercial 0.888
  Ø16: 1.5783 kg/m, regla 1.5782, tabla comercial 1.578
  Ø20: 2.4662 kg/m, regla 2.4660, tabla comercial 2.466
  Ø25: 3.8534 kg/m, regla 3.8531, tabla comercial 3.853
  Ø32: 6.3133 kg/m, regla 6.3130, tabla comercial 6.313

Servicio build_rebar_schedule: 5 entradas, total 117.14 kg, por Ø {8: {'total_kg': 2.56}, 10: {'total_kg': 39.98}, 16: {'total_kg': 27.62}, 20: {'total_kg': 46.98}}
  Entrada con n = 0 → ConfigurationError: Entrada invalida en marca '9'

Cuantía de la viga: 130 kg/m³ de hormigón (0.90 m³); los cercos son el 34 % del acero. Las longitudes de corte son dato: salen de `rebar_cut_length`, no de la planilla.
```

</details>

#### Quantità in kg/m³ per elemento con designazioni di Stati Uniti, Europa, Australia e Colombia

<details><summary>Output reale di <code>python examples/rebar_quantities_kg_per_m3_by_element_and_bar_designations_usa_eu_au_nsr.py</code></summary>

```text
Designación americana (ASTM A615):
  elemento acero [kg] hormigón [m³] cuantía [kg/m³]
       C-1      161.1         0.900             179
       C-2      100.2         0.576             174
       V-1      114.9         0.900             128
       Z-1      108.6         3.456              31
  Total del proyecto: 484.8 kg

Mismo armado en métrico (EU, Ø25/20/16/10):
       C-1      159.9 kg →   178 kg/m³
       C-2      110.1 kg →   191 kg/m³
       V-1      125.8 kg →   140 kg/m³
       Z-1      110.0 kg →    32 kg/m³
  Total: 505.8 kg (+4.3 % frente al americano: #8 = 25,4 mm y #3 = 9,5 mm no son Ø25 y Ø10 exactos)

Equivalencias y kg/m por código:
    USA Ø [mm]   kg/m |   EU   kg/m |   AU Ø [mm]   kg/m |  NSR Ø [mm]
     #3    9.5  0.556 |   10  0.617 |  N12     12  0.888 |   #3    9.5
     #4   12.7  0.994 |   12  0.888 |  N12     12  0.888 |   #4   12.7
     #5   15.9  1.559 |   16  1.578 |  N16     16  1.578 |   #5   15.9
     #6   19.1  2.249 |   20  2.466 |  N20     20  2.466 |   #6   19.1
     #8   25.4  3.978 |   25  3.853 |  N24     24  3.551 |   #8   25.4
    #10   32.3  6.432 |   32  6.313 |  N32     32  6.313 |   25   25.0

  Designación de otro código → ValueError: Designación N12 no encontrada para EU

Las cuantías orientativas de pilar (120–200 kg/m³), viga (90–150) y zapata (30–70) sirven para contrastar un despiece: un elemento fuera de rango suele tener una longitud o un conteo mal copiado. El módulo no deduce longitudes ni solapes; pesa lo que se le da.
```

</details>

#### Tabella degli acciai e tabella delle revisioni come geometria indipendente da ezdxf, disegnate nell'angolo di una tavola

<details><summary>Output reale di <code>python examples/schedule_block_and_revision_block_geometry_drawn_into_dxf_sheet_corner.py</code></summary>

```text
Cuadro de aceros: 5 marcas → 12 rectángulos/líneas, 42 textos, total 117.2 kg; caja 125 × 56 mm de papel en (600, 60)
  marca 1: Ø20 × 6350 mm × 3 = 19.05 m → 47.0 kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)
  marca 2: Ø16 × 6350 mm × 2 = 12.70 m → 20.1 kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)
  marca 3: Ø16 × 2400 mm × 2 = 4.80 m → 7.6 kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)
  marca 4: Ø10 × 1544 mm × 42 = 64.85 m → 40.0 kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)
  marca 5: Ø8 × 540 mm × 12 = 6.48 m → 2.6 kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)
  Cabeceras: ['Marca', 'φ (mm)', 'L (mm)', 'Cant.', 'Σ L (m)', 'Σ peso (kg)']; fila de totales: ['TOTAL', '117.2']

Cuadro de revisiones: 3 revisiones → 7 rectángulos/líneas, 16 textos; caja 135 × 32 mm

DXF cuadros_aceros_revisiones.dxf: {'LWPOLYLINE': 2, 'LINE': 17, 'TEXT': 58} (los dos cuadros en milímetros de papel, listos para pegar en un layout)

La geometría es una lista de rectángulos (alto 0 = línea horizontal, ancho 0 = vertical) y textos con posición y altura: se prueba sin ezdxf y se dibuja con cualquier backend. El cuadro de aceros aquí no deduce longitudes de corte ni solapes; pesa con 0,00617·Ø² (0,07 % sobre el exacto).
```

</details>

### 4. Tabelle, tavole, layer e scale

#### Tabella dei pilastri piani × pilastri con la sezione in scala in ogni cella: statistiche esatte e validazione

<details><summary>Output reale di <code>python examples/schedule_grid_column_schedule_three_columns_two_storeys_exact_entities_and_validation.py</code></summary>

```text
Cuadro 4 pilares × 4 plantas = 16 celdas (15 con pilar, 1 con «-»)
  Estadísticas: 132 líneas, 40 textos, 110 círculos → 282 entidades
  Círculos = Σ n_bars = 110 → coincide
  Líneas = cuadrícula (6 horizontales + 6 verticales) + 8 por celda con pilar (15) = 132 → coincide
  Textos = 1 + 4 + 4 + 2·15 + 1 = 40 → coincide
  DXF releído: {'LINE': 132, 'TEXT': 40, 'CIRCLE': 110}; capas ['S-COL-CONC', 'S-COL-LINE', 'S-COL-REBAR', 'S-COL-TEXT']
  Celda P-1 / Cimentación: ['50x50 cm - 12Ø25', '50x50 cm - 8Ø25'], ['e: Ø10 c/10cm']
  n_bars = 5 (impar) → ValueError: spec.n_bars must be an even integer >= 4 for symmetric column reinforc…
  n_bars = 2 (menos de 4) → ValueError: spec.n_bars must be at least 4, got 2 for X…

La miniatura reparte las barras intermedias solo en las caras superior e inferior: para 12Ø25 dibuja 4 esquinas + 4 + 4; el pilar rectangular 600 × 400 con 10 barras sale con 3 intermedias por cara larga. Es un cuadro de obra (dimensiones en cm, estribo en cm), no un despiece: el despiece va en `column_rebar_detail`.
```

</details>

#### Tavola A3 e A1 con cornice, cartiglio e finestra nello spazio carta contro il metodo precedente nello spazio modello

<details><summary>Output reale di <code>python examples/sheet_template_a3_a1_paperspace_layout_title_block_viewport_vs_legacy_modelspace.py</code></summary>

```text
Hoja A3 420 × 297 mm; layouts del documento: ['Model', 'Layout1', 'A3_Sheet']
  Espacio papel «A3_Sheet»: {'VIEWPORT': 2, 'LWPOLYLINE': 4, 'LINE': 5, 'TEXT': 25} (borde, marco, cajetín 3 × 4, logo, ventana); modelo: {'LINE': 8, 'HATCH': 1, 'CIRCLE': 12, 'TEXT': 3, 'DIMENSION': 1} (la sección del pilar en mm, intacta)
  Ventana: centro papel (140.0, 148.5) mm, tamaño 230 × 277 mm, vista del modelo centrada en (250, 250, 0) con altura 2770 mm → escala 1:10
  Cajetín: ['Edificio de oficinas — Bloque B', 'Promotora XYZ', 'S-301 Detalle pilar P-1', '1:10', 'B', 'JM']

Añadida una A1 al mismo documento: layouts ['Model', 'Layout1', 'A3_Sheet', 'A1_Sheet']; A1_Sheet tiene 36 entidades (cajetín de 180 × 50 mm en A1/A2/A0, 150 × 40 en A3/A4)
  Método heredado draw_in_modelspace: DeprecationWarning — «SheetTemplate.draw_in_modelspace() is deprecated; use SheetTemplate.apply_to_lay…»; añade 29 líneas al contador del modelo
  Tamaño desconocido → TemplateError: Tamano de hoja desconocido 'B2'

El cajetín en espacio papel se imprime a 1:1 y la escala la fija la ventana (view_height = alto de la ventana × denominador): para 1:10 en A3 la vista tiene 2770 mm de alto. El texto «v1.0» de la celda de marca es fijo y el logo es un hueco: dos detalles cosméticos que el usuario sustituye en su plantilla.
```

</details>

#### Modelli costruttivi come geometria pura (plinto, trave, pilastro, parete) composti in una tavola A1 e resi in DXF

<details><summary>Output reale di <code>python examples/construction_templates_geometry_without_ezdxf_footing_beam_column_wall_and_a1_sheet_render.py</code></summary>

```text
Plantillas (unidades mm del modelo):
  zapata 2500 × 2500 × 600, pilar 400 rect   2  círc  64  líneas   0  textos   2  → ['2500', '2500']
  viga 300 × 500, 3+3Ø16, est Ø10@200 rect   2  círc   6  líneas   0  textos   5  → ['300', '500', '3⌀16', '3⌀16']
  pilar 400 × 400, 3 × 3 → 8Ø20      rect   2  círc   8  líneas   0  textos   4  → ['400', '400', '8⌀20', 'Est ⌀10@150']
  muro 3000 × 200, borde 4Ø16, alma 6 rect   3  círc  14  líneas   0  textos   4  → ['3000', '200', 'Borde: 4⌀16', 'Alma: 6⌀16']
  cajetín A1 (bloque 180 × 80 mm)    rect   1  círc   0  líneas   3  textos   5  → ['Nave logística', 'Plano: E-02', 'Esc 1:50', 'Rev 1']
  La zapata lleva una parrilla fija de 8 × 8 = 64 puntos (representación, no cálculo); el pilar 3 × 3 da 8 barras perimetrales

Lámina A1 1:20 con cuatro detalles: 12 rectángulos, 92 círculos, 4 líneas, 21 textos; cajetín: ['PROYECTO: Nave logística', 'PLANO: Detalles de cimentación y pilares (E-02)', 'ESCALA: 1:20', 'REV: 1', 'AUTOR: JM', 'SOFTWARE: JMSTRUCTURAL']
DXF lamina_A1_detalles.dxf (AC1024): {'LINE': 52, 'CIRCLE': 92, 'TEXT': 21}; por capa {'BORDER': 16, 'GEOMETRY': 36, 'REBAR': 92, 'TEXT': 21} (los 3 primeros rectángulos y 4 primeras líneas van a BORDER)

Estas plantillas son geometría de referencia (parrilla fija, barras repartidas por reglas simples) pensada para tests y para componer láminas; el detalle normativo con A_s, separaciones y estados de cálculo está en `FoundationPlan`, `BeamDetail` y `ColumnDetail`.
```

</details>

#### Layer: registro in spagnolo con colore, tipo di linea e spessore, i 21 layer AIA e cinque standard di nomenclatura

<details><summary>Output reale di <code>python examples/layer_standards_aia_iso13567_corenet_natspec_ntc_and_apply_layers_colors_linetypes.py</code></summary>

```text
Registro estándar (14 capas):
  capa       color                linetype grosor [mm]  descripción
  CONCRETO       7 blanco/negro CONTINUOUS        0.50  Concrete outlines
  ARMADURA       2 amarillo     CONTINUOUS        0.35  Longitudinal rebar
  ACERO          2 amarillo     CONTINUOUS        0.35  Generic steel
  ESTRIBO        3 verde        CONTINUOUS        0.18  Stirrups / ties
  COTAS          4 cian         CONTINUOUS        0.13  Dimensions
  TEXTO          7 blanco/negro CONTINUOUS        0.18  Annotation text
  EJES           1 rojo             CENTER        0.13  Grid axes
  HATCH          8 gris oscuro  CONTINUOUS        0.09  Hatching / fills
  RELLENO        8 gris oscuro  CONTINUOUS        0.09  Concrete hatch
  CAJETIN        7 blanco/negro CONTINUOUS        0.50  Title block frame
  OCULTAS        8 gris oscuro      HIDDEN        0.13  Hidden lines
  AUXILIAR       8 gris oscuro      DASHED        0.09  Construction lines
  MURO           7 blanco/negro CONTINUOUS        0.50  Walls
  ZAPATA         7 blanco/negro CONTINUOUS        0.50  Footings

DXF capas_estandar.dxf: 37 capas (14 estándar + 21 AIA + «0» y «Defpoints»); linetypes disponibles: ['ByBlock', 'ByLayer', 'CENTER', 'Continuous', 'DASHDOT', 'DASHED']
  EJES         color 1 (rojo), linetype CENTER, grosor 0.13 mm
  OCULTAS      color 8 (gris oscuro), linetype CONTINUOUS, grosor 0.13 mm
  AUXILIAR     color 8 (gris oscuro), linetype DASHED, grosor 0.09 mm
  S-GRID       color 8 (gris oscuro), linetype DASHDOT, grosor 0.25 mm
  S-COLU-RBAR  color 1 (rojo), linetype Continuous, grosor 0.50 mm
  color_of('ARMADURA') = 2; capa desconocida → 7

Capas AIA / US National CAD Standard (21): patrón <Disciplina>-<Mayor>-<Menor>
  S-COLU-CONC  Columnas - Hormigón          color 3 verde        Continuous 0.25 mm
  S-COLU-RBAR  Columnas - Refuerzo          color 1 rojo         Continuous 0.50 mm
  S-BEAM-CONC  Vigas - Hormigón             color 5 azul         Continuous 0.25 mm
  S-BEAM-RBAR  Vigas - Refuerzo             color 1 rojo         Continuous 0.50 mm
  S-SLAB-CONC  Losas - Hormigón             color 4 cian         Continuous 0.25 mm
  S-SLAB-RBAR  Losas - Refuerzo             color 1 rojo         Continuous 0.25 mm
  S-WALL-CONC  Muros - Hormigón             color 6 magenta      Continuous 0.25 mm
  S-WALL-RBAR  Muros - Refuerzo             color 1 rojo         Continuous 0.25 mm
  … y 13 más (acero, conexiones, anotaciones, grilla); get_layer('S-FNDN-RBAR') → AIALayer(name='S-FNDN-RBAR', description='Fundaciones - Refuerzo', color_aci=1, linetype='Continuous', lineweight_mm=0.5)

Estándares de nomenclatura por país:
  AIA-NCS-US      AIA / US National CAD Standard             <DISCIPLINE>-<MAJOR>-<MINOR>-<STATUS>    ej. S-COLU-CONC
  ISO-13567-EU    ISO 13567 (Eurocode CAD layers)            A<SUBJECT><ELEMENT><PRESENTATION>        ej. A21S101
  BCA-CORENET-SG  Singapore CORENET BIM Layer Guide          <DISCIPLINE>_<ELEMENT>_<PROPERTY>        ej. S_COL_RBAR
  NATSPEC-AU      NATSPEC National BIM Guide (Australia)     <MODEL>-<CATEGORY>-<TYPE>                ej. ST-COL-CONC
  NTC-1960-CO     ICONTEC NTC 1960 (Colombia)                <DISCIPLINE>-<ELEMENT>-<PROPERTY>        ej. EST-COL-HOR
  ES: ISO-13567-EU → A21S101
  US: AIA-NCS-US → S-COLU-CONC
  SG: BCA-CORENET-SG → S_COL_RBAR
  AU: NATSPEC-AU → ST-COL-CONC
  CO: NTC-1960-CO → EST-COL-HOR
  BR: sin estándar asignado (devuelve None)
  lookup('ISO-13567-EU').example = A21S101

Un plano que mezcla las dos familias (CONCRETO y S-COLU-CONC) imprime bien pero confunde al que filtra por capas: elige una. Los códigos ISO 13567 (A21S101) solo se dan como patrón, el paquete no genera el catálogo completo de códigos de elemento.
```

</details>

#### Scale: la scala che fa entrare un disegno in un foglio, altezze del testo e distanze delle quote in unità del modello

<details><summary>Output reale di <code>python examples/scales_auto_scale_for_sheets_text_heights_dimension_offsets_and_bbox_table.py</code></summary>

```text
Serie de escalas: (10, 20, 25, 50, 75, 100, 200, 250, 500, 1000); hojas ISO 216 [mm]: {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594), 'A0': (1189, 841)}

  dibujo                             hoja área útil [mm] necesaria escala texto 2,5 mm → modelo cota 7 mm flecha 2,5
  planta de cimentación 24 × 15 m      A1      781 × 534      30.7   1:50                 125.0     350.0      125.0
  planta de cimentación 24 × 15 m      A3      360 × 237      66.7   1:75                 187.5     525.0      187.5
  planta de cimentación 24 × 15 m      A4      237 × 150     101.3  1:200                 500.0    1400.0      500.0
  alzado de pórtico 17 × 10 m          A1      781 × 534      21.8   1:25                  62.5     175.0       62.5
  alzado de pórtico 17 × 10 m          A3      360 × 237      47.2   1:50                 125.0     350.0      125.0
  alzado de pórtico 17 × 10 m          A4      237 × 150      71.7   1:75                 187.5     525.0      187.5
  sección de viga 0,5 × 0,6 m          A1      781 × 534       1.1   1:10                  25.0      70.0       25.0
  sección de viga 0,5 × 0,6 m          A3      360 × 237       2.5   1:10                  25.0      70.0       25.0
  sección de viga 0,5 × 0,6 m          A4      237 × 150       4.0   1:10                  25.0      70.0       25.0
  detalle de gancho 0,12 × 0,08 m      A1      781 × 534       0.2   1:10                  25.0      70.0       25.0
  detalle de gancho 0,12 × 0,08 m      A3      360 × 237       0.3   1:10                  25.0      70.0       25.0
  detalle de gancho 0,12 × 0,08 m      A4      237 × 150       0.5   1:10                  25.0      70.0       25.0

Conversiones papel ↔ modelo:
  1:20: 100 mm de papel = 2000 mm de modelo; una viga de 6000 mm mide 300 mm en el papel; texto 3,5 mm → 70 mm
  1:50: 100 mm de papel = 5000 mm de modelo; una viga de 6000 mm mide 120 mm en el papel; texto 3,5 mm → 175 mm
  1:100: 100 mm de papel = 10000 mm de modelo; una viga de 6000 mm mide 60 mm en el papel; texto 3,5 mm → 350 mm
  Modelo en metros, 1:50: 6 m de viga = 120 mm de papel; 2,5 mm de texto = 0.1250 m de modelo

  bbox_of de 5 puntos → (0.0, 0.0, 24000.0, 16500.0) → 24000 × 16500 mm → auto_scale A1 = 1:50
  Hoja desconocida → ValueError: Unknown sheet 'A5'. Use one of ['A4', 'A3', 'A2', 'A1', 'A0'].

La planta de 24 m pide 1:50 en A1, 1:75 en A3 (la serie incluye el 75; muchas oficinas lo evitan y saltan a 1:100) y 1:200 en A4; la sección entra a 1:10 en cualquier hoja porque 1:10 es la escala más grande de la serie. Las alturas de texto son las que hay que pasar a `DXFDocument.text` para que el plano impreso tenga 2,5 mm: dibujar en mm de modelo con texto de 2,5 mm sale ilegible a 1:50.
```

</details>

### 5. Esportazione, integrazioni, API e stato di calcolo

#### Salvare nella versione DXF richiesta dal visualizzatore (da R2000 a R2018), verificare con audit e verify ed eliminare i blocchi inutilizzati

<details><summary>Output reale di <code>python examples/export_save_dxf_pinned_versions_r2000_to_r2018_audit_verify_and_clean.py</code></summary>

```text
Documento de ezdxf creado por ColumnDetail: versión AC1032 (R2018), 21 entidades en el modelo

  pedida  fichero   leído    ok errores arreglos entidades   bytes
   R2000 P-5_R2000.dxf   R2000  True       0        0        21   23557
   R2004 P-5_R2004.dxf   R2004  True       0        0        21   24001
   R2007 P-5_R2007.dxf   R2007  True       0        0        21   25277
   R2010 P-5_R2010.dxf   R2010  True       0        0        21   25315
   R2013 P-5_R2013.dxf   R2013  True       0        0        21   25349
   R2018 P-5_R2018.dxf   R2018  True       0        0        21   25347
  Las seis versiones llevan las mismas 21 entidades; el fichero crece con la versión por las tablas y objetos que añade cada formato.

  Versión no soportada → ConfigurationError: dxfversion 'R2025' no soportada. Use una de ('R2000', 'R2004', 'R2007', 'R2010', 'R2013', …

clean(): bloques antes ['BLQ_USADO', 'BLQ_HUERFANO_1', 'BLQ_HUERFANO_2'] → purgados 2 → quedan ['BLQ_USADO'] (el referenciado por INSERT se conserva)
  guardado como R2010 → verify {'ok': True, 'errors': 0, 'fixes': 0, 'dxfversion': 'AC1024', 'n_modelspace_entities': 1}

R2010 es la versión segura para intercambio (Revit Link CAD, visores antiguos, CNC de ferralla); R2018 solo si hace falta algo de las versiones nuevas. El auditor arregla lo que puede (handles, tablas) y lo demás lo cuenta como error en `verify`.
```

</details>

#### Collegamento da un progetto di sezione ferro per ferro al DXF con quote e annotazioni

<details><summary>Output reale di <code>python examples/integration_fastsap_bridge_rc_section_design_to_dxf_bars_layout_as_and_notes.py</code></summary>

```text
Sección P-12 500 × 600, recubrimiento 40, estribo Ø10@150: 10 barras Ø25 = 2·3 + 2·(4 − 2)
  Centro de la primera barra a c + Ø_e + Ø/2 = 62.5 mm del borde; posiciones (x, y): [(62, 62), (62, 221), (62, 379), (62, 538), (250, 62), (250, 538), (438, 62), (438, 221), (438, 379), (438, 538)]
  Resultado: 10 barras, A_s = 4909 mm² (a mano 4909), ρ = 1.64 %; notas ['As_total = 4909 mm2', 'rho = 1.636%', '10 barras phi25']
  DXF P-12_bridge.dxf: {'LWPOLYLINE': 2, 'CIRCLE': 10, 'HATCH': 10, 'TEXT': 7}; capas ['CONCRETE', 'DIM', 'REBAR', 'TEXT', 'TIE']; textos ['b = 500 mm', 'h = 600 mm', 'Section: P-12', '10 bars phi25 mm', 'As = 4909 mm2 (rho = 1.64%)', 'Stirrups phi10@150 mm', 'fc = 30 MPa, fy = 500 MPa']

Viga V-7 con barras colocadas a mano (2Ø20 + 1Ø16 abajo, 2Ø16 arriba): A_s = 1232 mm²; radios dibujados [8.0, 10.0] mm → aquí sí se respeta cada diámetro (lo que `BeamDetail` no hace)
  Aviso: la anotación del bloque de texto dice «5 bars phi20» tomando el Ø de la primera barra; con diámetros mezclados hay que leer A_s, no esa línea.
  n_bars_x = 1 → ValueError: n_bars_x y n_bars_y deben ser >= 2
  recubrimiento + estribo + barra ≥ b/2 → ValueError: cover+tie+bar excede media seccion: imposible armar
  b negativo → ValueError: dimensiones deben ser positivas
  Sección sin barras → ValueError: design sin barras: nada que dibujar

El puente no importa el dimensionador: cualquier programa que entregue barras con (x, y, Ø) puede pintar su sección. Las capas aquí son CONCRETE/REBAR/TIE/DIM/TEXT (inglés), distintas del registro CONCRETO/ARMADURA del resto del paquete.
```

</details>

#### DXF adatto a Revit Link CAD: entità 2D, $INSUNITS, stile SHX, layer AIA e rifiuto dei solidi

<details><summary>Output reale di <code>python examples/integration_revit_link_cad_dxf_2d_entities_insunits_shx_style_and_forbidden_3dsolid.py</code></summary>

```text
30 entidades neutras → planta_revit_link.dxf: versión AC1024 (R2010), $INSUNITS = 4 (4 = milímetros)
  Entidades: {'LINE': 5, 'CIRCLE': 3, 'TEXT': 10, 'LWPOLYLINE': 12} (solo LINE, LWPOLYLINE, CIRCLE, TEXT)
  Estilo de texto REVIT_STD → fuente «txt.shx» (SHX, no TrueType); textos con ese estilo: 10 de 10
  Capas y color (prefijo AIA): S-GRID=7, S-GRID-IDEN=7, S-COLU-CONC=1, S-FNDN-CONC=4, S-TEXT=7, S-ANNO-TEXT=6
  Mapa AIA_COLORS: {'S-COLU': 1, 'S-BEAM': 2, 'S-SLAB': 3, 'S-FNDN': 4, 'S-WALL': 5, 'S-DIMS': 7, 'S-TEXT': 7, 'S-ANNO': 6}

  Entidad 3DSOLID → ValueError: Entidad '3DSOLID' no compatible con Revit Link CAD.
  Entidad SPLINE (no soportada) → ValueError: Tipo de entidad no soportado: SPLINE

Misma planta en metros: $INSUNITS = 6 (6 = metros), fuente simplex.shx, color de S-FNDN-CONC sobrescrito a 30
  Unidades no soportadas → ValueError: Unidades 'FT' no soportadas (use MM o M).

Revit vincula bien si las unidades del DXF coinciden con las del import (mm o m), no hay 3D ni XREF y las fuentes son SHX; los colores por capa se mantienen al vincular y se pierden al explotar. El puente no convierte un plano existente: recibe entidades neutras.
```

</details>

#### API REST senza server: pilastro, trave, pianta e parete via POST, DXF in base64 o come file, e 422 con geometria non valida

<details><summary>Output reale di <code>python examples/rest_api_drawings_column_beam_footing_wall_testclient_json_base64_file_and_422.py</code></summary>

```text
C:\Users\jesus\AppData\Local\Temp\jmv\rebardxf\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
API «RebarDXF REST API» v1.2.0; GET /api/drawings/health → {'status': 'ok', 'service': 'rebardxf'}

POST /column (12Ø20) → 200; 25851 bytes en base64, entidades {'lines': 8, 'circles': 12, 'texts': 3, 'rects': 2}, resumen ρ = 1.508 %, A_s = 3769.9 mm²; DXF decodificado: {'LINE': 8, 'HATCH': 1, 'CIRCLE': 12, 'TEXT': 3, 'DIMENSION': 1}
POST /beam?format=file → 200, application/dxf, 22322 bytes, empieza por b'  0\r\nSECTION'
POST /footing (2 zapatas) → 200; cuadro: Z-1 CALCULADO_CUMPLE; Z-2 NO_CALCULADO; 58 entidades
POST /wall → 200; ρ_be = 1.496 %, ρ_v = 0.503 %, check_v = True
  column con recubrimiento ≥ b/2 → 422: cover_mm fuera de rango
  beam con sin barras superiores → 422: Debe especificar bars_top y bars_bot
  footing con sin zapatas → 422: Debe haber al menos una zapata
  wall con bordes que no caben → 422: Los elementos de borde no caben en el muro
  format=pdf → 422 (solo json|file)

La API escribe cada DXF en un directorio temporal y lo devuelve; no guarda estado ni autentica: es para montar detrás de un gateway o para pruebas. Sin endpoints de despiece de pilar/zapata ni de cuadro de pilares: esos van por los servicios de Python.
```

</details>

#### Lo stato di un calcolo non è un booleano: `resolve_status` chiuso per default e aggregazione senza verità vacua

<details><summary>Output reale di <code>python examples/audit_status_resolve_and_aggregate_closed_by_default_no_silent_pass.py</code></summary>

```text
../scripts_repos/run_examples.sh: line 14: $PY: command not found
```

</details>

## Verifica

- Conteggio esatto delle entità DXF rilette con ezdxf nel prospetto del telaio (formula chiusa di linee, cerchi e testi), nella tabella dei pilastri (cerchi = Σ ferri) e negli invarianti del documento (`tests/test_golden_analytical_dxf_detailing.py`, `test_golden_column_schedule_grid.py`, `test_frame_elevation_exact_entities.py`, `test_golden_dxf_invariants.py`).
- Lunghezze di taglio e diametri di piegatura contro la ACI 318-19 §25.3, l'ACI Detailing Manual e la BS 8666 con sviluppo a mano; massa lineare π·Ø²/4·7850 e conservazione della massa nella distinta (`test_golden_fichas_dxf_structural.py`, `test_rebar_cut_length.py`, `test_bend_diameters.py`).
- Plinti: i ferri disegnati, l'etichetta della tavola e la tabella coincidono per costruzione (A_b·(w/s + 1)/B = A_b/s_rot·1000 ≥ A_s) e un plinto senza A_s o senza Ø non disegna alcun ferro (`test_footing_rebar_derivation_c3.py`, `test_uncalculated_footing_rebar.py`, `test_footing_spec_not_preapproved.py`).
- Correzioni della 1.2.0, ognuna con il proprio test: disposizione perimetrale senza ferri sovrapposti per 4–24 ferri in tre rapporti di forma, e `save_dxf` che scrive la versione richiesta (`test_column_layout_no_duplicate_bars.py`, `test_save_dxf_pins_version.py`); test di proprietà con hypothesis sui servizi.
- `tests/test_examples.py` esegue i 25 esempi come sottoprocessi su ubuntu e windows × Python 3.11–3.13.

## Limitazioni

- Non dimensiona: A_s, ancoraggi, sovrapposizioni e lunghezze dei ferri sono dati del progettista; il pacchetto distribuisce, verifica interassi e percentuali minime e disegna.
- `BeamDetail` disegna ogni strato con il diametro maggiore del gruppo (una sola posizione per ferro, senza distinguere i diametri); `ColumnDetail` disegna il Ø maggiore e ripete una posizione con un totale dispari; `column_rebar_detail` disegna tutti i ferri del perimetro nelle sezioni e una linea per posizione nel prospetto; `column_schedule_grid` distribuisce i ferri intermedi solo sulle facce superiore e inferiore. Per diametri misti usa `integration.fastsap_bridge.RCSectionDesign`.
- `FootingData.s_commercial_step_mm` è accettato ma l'etichetta arrotonda al millimetro; il copriferro predefinito è 75 mm (ACI 318-19 Tabella 20.5.1.3.1, contro terra) e s_max usa 3h senza il limite di 2h delle solette; `rebar_schedule_block.RebarItem` pesa con 0,00617·Ø² (0,07 % sopra il valore esatto); le forme L, U e S di `rebar_shapes` non accettano `bar=` e usano il raggio precedente (3Ø, 4Ø, 5Ø).
- I layer convivono in due famiglie (CONCRETO/ARMADURA e S-COLU-CONC/S-COLU-RBAR) e il collegamento di sezione ne usa una terza (CONCRETE/REBAR/TIE); `templates_construction` scrive «SOFTWARE: JMSTRUCTURAL» e `SheetTemplate` «v1.0» nel cartiglio; i codici ISO 13567 si danno come schema, non come catalogo.
- `DXFDocument.dimension_linear` e `hatch_concrete` inghiottono le eccezioni di ezdxf (se lo stile di quota non esiste, la quota sparisce senza avviso): controlla il conteggio di DIMENSION/HATCH con `verify` o rileggendo il file.
- L'API REST non autentica né conserva stato e non espone la tavola di dettaglio di pilastri/plinti né la tabella dei pilastri; l'invio in tempo reale ad AutoCAD (`integration.autocad_live`) richiede Windows, pyautocad e una sessione aperta, e non è esercitato negli esempi.

## Norme e riferimenti

- ACI 318-19: §25.3 (uncini e diametri di piegatura), §25.2.1 (interasse minimo), §13.3.2.1 e §7.7.2.3 (interasse massimo nelle fondazioni), §18.6.4 e §18.7.5 (zone confinate), §11.6 (percentuali delle pareti), Tabella 20.5.1.3.1 (copriferri); ACI 315R-18 e ACI Detailing Manual; CRSI Manual of Standard Practice.
- EN 1992-1-1:2004 §8.2 (interasse minimo), §9.3.1.1 (interasse massimo), §8.4 e §8.5 (ancoraggi, come riferimento dei test); EN 1998-1 §5.4.3 (pareti).
- BS 8666 (codici di forma e lunghezze di taglio); EN ISO 3766 (rappresentazione semplificata delle armature); ASTM A615 (designazioni da #3 a #18).
- ISO 216 (formati dei fogli); AIA CAD Layer Guidelines / US National CAD Standard; ISO 13567; BCA CORENET BIM Layer Guide; NATSPEC National BIM Guide; ICONTEC NTC 1960.
- Autodesk DXF Reference (R2018); Autodesk Revit «Importing CAD» (Link CAD); documentazione di ezdxf.

## Licenza

MIT. Vedi [LICENSE](LICENSE).

---

Parte di **Loadpath**, la raccolta di librerie strutturali open source di [Jesús Murgas](https://github.com/jmurgass99).
