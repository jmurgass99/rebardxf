// C++ / WebAssembly kernel para área de barra de refuerzo y longitud básica de anclaje ACI 318 / EC2
extern "C" {
  double barAreaMm2(double db_mm) {
    return 0.7853981633974483 * db_mm * db_mm;
  }

  double anchorageLengthMm(double db_mm, double fyd_mpa, double fbd_mpa) {
    return (db_mm / 4.0) * (fyd_mpa / fbd_mpa);
  }
}
