
import json
from pathlib import Path

import cv2

# Ruta absoluta a datos/regiones.json, calculada desde la ubicación de este
# archivo (procesamiento/regiones.py). Así funciona sin importar desde qué
# carpeta se ejecute el programa.
RUTA_REGIONES = Path(__file__).resolve().parent.parent / "datos" / "regiones.json"

# Orden de prioridad al clasificar. Si dos zonas se solapan, gana la primera.
PRIORIDAD_ZONAS = ("atencion", "espera")

# Colores en formato BGR (así los usa OpenCV)
COLOR_ALERTA = (0, 0, 255)  # rojo

# Datos de cada zona: texto para calibrar, etiqueta en pantalla y color
ZONAS = {
    "espera": {
        "titulo": "ZONA DE ESPERA",
        "etiqueta": "ESPERA",
        "color": (0, 165, 255),  # naranja
    },
    "atencion": {
        "titulo": "ZONA DE ATENCION",
        "etiqueta": "ATENCION",
        "color": (0, 255, 0),  # verde
    },
}


def hay_solape(region_a, region_b):
    """Devuelve True si dos rectángulos [x, y, ancho, alto] se superponen."""
    ax, ay, aancho, aalto = region_a
    bx, by, bancho, balto = region_b

    separados = (
        ax + aancho <= bx
        or bx + bancho <= ax
        or ay + aalto <= by
        or by + balto <= ay
    )
    return not separados


def seleccionar_regiones(frame):
    """Pide al usuario dibujar cada zona con el mouse y guarda el resultado."""
    RUTA_REGIONES.parent.mkdir(parents=True, exist_ok=True)

    regiones = {}

    for clave, datos in ZONAS.items():
        titulo = datos["titulo"]

        while True:
            print(
                f"\nSelecciona la {titulo} arrastrando el mouse "
                "y presiona ENTER (o 'c' para cancelar)."
            )

            x, y, ancho, alto = cv2.selectROI(
                titulo, frame, showCrosshair=True, fromCenter=False
            )
            cv2.destroyWindow(titulo)

            if ancho > 0 and alto > 0:
                regiones[clave] = [int(x), int(y), int(ancho), int(alto)]
                break

            print("No seleccionaste una región válida. Intenta nuevamente.")

    # Aviso útil: las zonas solapadas hacen más difícil interpretar los tiempos
    if hay_solape(regiones["espera"], regiones["atencion"]):
        print(
            "\nAVISO: las zonas de espera y atención se superponen. "
            "En el área compartida se considerará ATENCION. "
            "Para resultados más claros, recalibra sin solapar."
        )

    with open(RUTA_REGIONES, "w", encoding="utf-8") as archivo:
        json.dump(regiones, archivo, indent=4)

    print("\nRegiones guardadas correctamente.")
    return regiones


def cargar_regiones():
    """Lee las regiones guardadas. Devuelve None si no existen o son inválidas."""
    if not RUTA_REGIONES.exists():
        print("El archivo de regiones no existe. Debes seleccionarlas primero.")
        return None

    try:
        with open(RUTA_REGIONES, "r", encoding="utf-8") as archivo:
            regiones = json.load(archivo)
    except json.JSONDecodeError:
        print("El archivo regiones.json está dañado. Vuelve a calibrar las zonas.")
        return None

    # Verificar que estén todas las zonas esperadas
    faltantes = [clave for clave in ZONAS if clave not in regiones]
    if faltantes:
        print(f"Faltan zonas en regiones.json: {faltantes}. Vuelve a calibrar.")
        return None

    return regiones


def dibujar_regiones(frame, regiones, zonas_en_alerta=None):
    """
    Dibuja las zonas sobre el frame.
    zonas_en_alerta: conjunto con nombres de zonas que deben verse en rojo
    (por ejemplo {"espera"} cuando se supera el tiempo límite).
    """
    if not regiones:
        return frame

    zonas_en_alerta = zonas_en_alerta or set()

    for clave, (x, y, ancho, alto) in regiones.items():
        datos = ZONAS.get(clave, {"etiqueta": clave.upper(), "color": (255, 255, 255)})

        en_alerta = clave in zonas_en_alerta
        color = COLOR_ALERTA if en_alerta else datos["color"]
        grosor = 4 if en_alerta else 2

        cv2.rectangle(frame, (x, y), (x + ancho, y + alto), color, grosor)
        cv2.putText(
            frame,
            datos["etiqueta"],
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    return frame


def obtener_zona(persona, regiones):
    """
    Devuelve la zona ("atencion", "espera" o "fuera") donde está la persona.
    Se usa el punto inferior central de la caja (los pies), que representa
    mejor dónde está parada que el centro de la caja.
    """
    if not regiones:
        return "fuera"

    x1, y1, x2, y2 = persona["caja"]
    punto_x = int((x1 + x2) / 2)
    punto_y = int(y2)

    for clave in PRIORIDAD_ZONAS:
        if clave not in regiones:
            continue

        rx, ry, rancho, ralto = regiones[clave]
        if rx <= punto_x <= rx + rancho and ry <= punto_y <= ry + ralto:
            return clave

    return "fuera"
