
import cv2
 
FUENTE = cv2.FONT_HERSHEY_SIMPLEX
 
ANCHO_PANEL = 440
MARGEN = 10
ALTO_LINEA = 28
 
 
def _panel_translucido(frame, x1, y1, x2, y2, color=(30, 30, 30), opacidad=0.7):
    """Pinta un rectángulo semitransparente, para que el video se siga viendo."""
    alto, ancho = frame.shape[:2]
    x1, y1 = max(x1, 0), max(y1, 0)
    x2, y2 = min(x2, ancho), min(y2, alto)
 
    zona = frame[y1:y2, x1:x2]
    fondo = zona.copy()
    fondo[:] = color
    frame[y1:y2, x1:x2] = cv2.addWeighted(fondo, opacidad, zona, 1 - opacidad, 0)
 
 
def _segundos(valor):
    """Texto para un tiempo en segundos; '--' si todavía no hay dato."""
    return "--" if valor is None else f"{valor:.0f} s"
 
 
def dibujar_dashboard(frame, estado):
    """
    estado: diccionario con
      personas_espera, personas_atencion   clientes en cada zona ahora
      personas_detectadas, total_observado conteo de personas
      resumen                              diccionario de Metricas.obtener_resumen()
      alertas                              lista de IDs que superaron el límite
      limite_espera                        segundos del límite
    """
    alto, ancho = frame.shape[:2]
    resumen = estado["resumen"]
 
    if resumen["total_esperas"] > 0:
        espera_prom = f"{_segundos(resumen['promedio_espera'])} ({resumen['total_esperas']})"
    else:
        espera_prom = "-- (sin datos)"
 
    if resumen["total_atenciones"] > 0:
        atencion_prom = f"{_segundos(resumen['promedio_atencion'])} ({resumen['total_atenciones']})"
    else:
        atencion_prom = "-- (sin datos)"
 
    lineas = [
        f"CLIENTES EN ESPERA: {estado['personas_espera']}",
        f"CLIENTES EN ATENCION: {estado['personas_atencion']}",
        f"DETECTADAS: {estado['personas_detectadas']}  |  TOTAL: {estado['total_observado']}",
        f"ESPERA PROMEDIO: {espera_prom}",
        f"ATENCION PROMEDIO: {atencion_prom}",
        f"ESPERA ESTIMADA: {_segundos(resumen['espera_estimada'])}",
        f"ABANDONOS: {resumen['abandonos']}",
    ]
 
    # Panel de métricas
    y_fin = MARGEN + 16 + ALTO_LINEA * len(lineas)
    _panel_translucido(frame, MARGEN, MARGEN, MARGEN + ANCHO_PANEL, y_fin)
 
    y = MARGEN + 28
    for texto in lineas:
        cv2.putText(frame, texto, (MARGEN + 15, y), FUENTE, 0.55, (255, 255, 255), 2)
        y += ALTO_LINEA
 
    # Alerta de espera prolongada (sin tildes: OpenCV no las dibuja bien)
    if estado["alertas"]:
        texto = f"ALERTA: ESPERA > {estado['limite_espera']} s ({len(estado['alertas'])})"
        (w, h), _ = cv2.getTextSize(texto, FUENTE, 0.8, 2)
 
        x2 = ancho - MARGEN
        x1 = x2 - w - 30
        y1 = MARGEN
 
        # Si no cabe al lado del panel, se coloca justo debajo de él
        if x1 < MARGEN + ANCHO_PANEL + MARGEN:
            x1 = MARGEN
            x2 = x1 + w + 30
            y1 = y_fin + MARGEN
 
        cv2.rectangle(frame, (x1, y1), (x2, y1 + h + 24), (0, 0, 200), -1)
        cv2.putText(frame, texto, (x1 + 15, y1 + h + 10), FUENTE, 0.8, (255, 255, 255), 2)
 
    return frame
 
