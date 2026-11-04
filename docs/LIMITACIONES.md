# Limitaciones conocidas de rebardxf

Lo que el paquete no hace o hace de forma simplificada.

- No dimensiona: A_s, anclajes, solapes y longitudes de barra son datos del calculista; el paquete reparte, comprueba separaciones y cuantías mínimas y dibuja.
- `BeamDetail` dibuja cada capa con el mayor diámetro del grupo (una sola posición por barra, sin distinguir diámetros); `ColumnDetail` dibuja el mayor Ø y repite una posición con un total impar; `column_rebar_detail` dibuja todas las barras del perímetro en los cortes y una línea por marca en el alzado; `column_schedule_grid` reparte las barras intermedias solo en las caras superior e inferior. Para diámetros mezclados usa `integration.fastsap_bridge.RCSectionDesign`.
- `FootingData.s_commercial_step_mm` se acepta pero el rótulo redondea al milímetro; el recubrimiento por defecto es 75 mm (ACI 318-19 Tabla 20.5.1.3.1, contra el terreno) y s_máx usa 3h sin el límite de 2h de losas; `rebar_schedule_block.RebarItem` pesa con 0,00617·Ø² (0,07 % sobre el exacto); las formas L, U y S de `rebar_shapes` no aceptan `bar=` y usan el radio heredado (3Ø, 4Ø, 5Ø).
- Las capas conviven en dos familias (CONCRETO/ARMADURA y S-COLU-CONC/S-COLU-RBAR) y el puente de sección usa una tercera (CONCRETE/REBAR/TIE); `templates_construction` escribe «SOFTWARE: JMSTRUCTURAL» y `SheetTemplate` «v1.0» en el cajetín; los códigos ISO 13567 se dan como patrón, no como catálogo.
- `DXFDocument.dimension_linear` y `hatch_concrete` tragan excepciones de ezdxf (si el estilo de cota no existe, la cota desaparece sin aviso): comprueba el recuento de DIMENSION/HATCH con `verify` o releyendo el fichero.
- La API REST no autentica ni guarda estado y no expone el despiece de pilar/zapata ni el cuadro de pilares; el envío en vivo a AutoCAD (`integration.autocad_live`) necesita Windows, pyautocad y una sesión abierta, y no se ejerce en los ejemplos.
