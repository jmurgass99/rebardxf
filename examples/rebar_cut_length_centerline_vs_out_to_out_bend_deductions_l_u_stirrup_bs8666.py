"""Longitud de corte de barras dobladas: fibra neutra frente a cotas exteriores, deducción por doblez y tres formas típicas (L, U, cerco cerrado) con el D de ACI 318-19 §25.3.

La longitud de corte se mide por el eje de la barra: tramos rectos + arcos θ·(r + Ø/2). Si el
despiece se cota out-to-out, hay que restar en cada doblez la deducción 2·(r + Ø)·tan(θ/2) − arco
(BS 8666, ACI Detailing Manual). Se tabulan arco y deducción a 90° y 135° para Ø8–Ø25 con D de
cerco (4Ø/6Ø) y de gancho estándar (6Ø/8Ø), y se calculan una barra en L (código 11), una U (21)
y un cerco cerrado 300 × 500 con ganchos de 135° (51) por los dos caminos.

Ejecutar:  python examples/rebar_cut_length_centerline_vs_out_to_out_bend_deductions_l_u_stirrup_bs8666.py
"""
from rebardxf.rebar_cut_length import bend_arc_length, bend_deduction, cut_length_centerline, cut_length_from_outside
from rebardxf.rebar_shapes import hook_extension, min_bend_diameter_aci


def main() -> None:
    print("Arco por la fibra neutra y deducción out-to-out por doblez [mm]:")
    print(f"  {'Ø':>3} {'D cerco':>7} {'arco 90°':>8} {'ded. 90°':>8} {'arco 135°':>9} {'ded. 135°':>9} | {'D gancho':>8} {'arco 90°':>8} {'ded. 90°':>8} {'arco 180°':>9}")
    for db in (8.0, 10.0, 12.0, 16.0, 20.0, 25.0):
        Dc = min_bend_diameter_aci(db, "stirrup_135")
        Dg = min_bend_diameter_aci(db, "standard_90")
        print(f"  {db:3.0f} {Dc:7.1f} {bend_arc_length(90, Dc, db):8.1f} {bend_deduction(90, Dc, db):8.1f} {bend_arc_length(135, Dc, db):9.1f} {bend_deduction(135, Dc, db):9.1f} | "
              f"{Dg:8.1f} {bend_arc_length(90, Dg, db):8.1f} {bend_deduction(90, Dg, db):8.1f} {bend_arc_length(180, Dg, db):9.1f}")
    print("  La deducción a 90° crece con Ø y con D: para Ø16 de gancho (D = 96) son 40 mm por esquina, el error clásico de la planilla que suma cotas exteriores.\n")

    # Barra en L (código 11): cotas exteriores A = 1200, B = 400, Ø16, D de gancho estándar
    db, D = 16.0, min_bend_diameter_aci(16.0, "standard_90")
    A, B = 1200.0, 400.0
    r = D / 2
    legs_eje = [A - (r + db), B - (r + db)]  # tramos rectos al eje = cota exterior − (r + Ø)
    L_eje = cut_length_centerline(legs_eje, [90.0], D, db)
    L_oto = cut_length_from_outside([A, B], [90.0], D, db)
    print(f"Barra en L (código 11) Ø16, cotas exteriores {A:.0f} + {B:.0f}, D = {D:.0f} mm (r = {r:.0f}):")
    print(f"  tramos rectos al eje {legs_eje[0]:.0f} + {legs_eje[1]:.0f} + arco {bend_arc_length(90, D, db):.1f} = {L_eje:.1f} mm; desde cotas exteriores {A + B:.0f} − {bend_deduction(90, D, db):.1f} = {L_oto:.1f} mm → {'coinciden' if abs(L_eje - L_oto) < 1e-9 else 'difieren'}; suma ingenua de cotas: {A + B:.0f} (+{A + B - L_eje:.0f} mm de más)")

    # Barra en U (código 21): A = 240 (ancho exterior), B = C = 450, Ø12, D de gancho
    db, D = 12.0, min_bend_diameter_aci(12.0, "standard_90")
    r = D / 2
    A, B = 240.0, 450.0
    L_u = cut_length_from_outside([B, A, B], [90.0, 90.0], D, db)
    print(f"\nBarra en U (código 21) Ø12, cotas {B:.0f} + {A:.0f} + {B:.0f}, D = {D:.0f}: longitud de corte {L_u:.1f} mm = {2 * B + A:.0f} − 2·{bend_deduction(90, D, db):.1f}")

    # Cerco cerrado 300 × 500, recubrimiento 30, Ø10, cuatro dobleces de 90° + dos ganchos de 135° con cola 6Ø ≥ 75
    db, D = 10.0, min_bend_diameter_aci(10.0, "stirrup_135")
    b, h, c = 300.0, 500.0, 30.0
    ext_b, ext_h = b - 2 * c, h - 2 * c  # cotas exteriores del cerco
    cola = hook_extension(db, 135)
    r = D / 2
    rectos = [ext_b - 2 * (r + db), ext_h - 2 * (r + db), ext_b - 2 * (r + db), ext_h - 2 * (r + db)]
    L_cerco = cut_length_centerline(rectos, [90.0, 90.0, 90.0, 135.0, 135.0], D, db, hook_tails_mm=[cola, cola])
    L_perimetro = 2 * (ext_b + ext_h)
    print(f"\nCerco cerrado (código 51) {ext_b:.0f} × {ext_h:.0f} exteriores (sección {b:.0f} × {h:.0f}, c = {c:.0f}), Ø10, D = {D:.0f} mm, colas de 135° = {cola:.0f} mm:")
    print(f"  4 tramos rectos al eje {[round(x) for x in rectos]} + 3 arcos de 90° + 2 arcos de 135° + 2 colas = {L_cerco:.0f} mm; perímetro exterior {L_perimetro:.0f} + 2 colas = {L_perimetro + 2 * cola:.0f} (la planilla rápida); diferencia {L_perimetro + 2 * cola - L_cerco:+.0f} mm")
    print(f"  Peso por cerco Ø10: {7850 * 3.14159 * 0.01 ** 2 / 4 * L_cerco / 1000:.3f} kg; en una viga con 60 cercos la planilla rápida pide {(L_perimetro + 2 * cola - L_cerco) * 60 / 1000:.1f} m de más.")
    print("\nMedir por la fibra neutra o restar la deducción es lo mismo; sumar cotas exteriores no. Con D pequeño (cercos Ø10, D = 40) la diferencia son milímetros por pieza; con Ø25 y D = 150 son 6 cm por doblez, 12 cm en una barra en U.")


if __name__ == "__main__":
    main()
