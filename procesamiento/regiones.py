import cv2
import json
from pathlib import Path

def seleccionar_regiones(frame):
    ruta = Path("datos/regiones.json")
    ruta.parent.mkdir(parents=True, exist_ok=True)

    regiones = {}

    nombres = {
        "espera": "ZONA DE ESPERA",
        "atencion": "ZONA DE ATENCION"
    }

    for clave, titulo in nombres.items():
        while True:
            print(f"\nSelecciona la {titulo} arrastrando el mouse y presiona ENTER (o 'c' para cancelar).")

            x, y, ancho, alto = cv2.selectROI(
                titulo,
                frame,
                showCrosshair=True,
                fromCenter=False
            )

            cv2.destroyWindow(titulo)

            if ancho > 0 and alto > 0:
                regiones[clave] = [
                    int(x), int(y), int(ancho), int(alto)
                ]
                break

            print("No seleccionaste una región válida. Intenta nuevamente.")

    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(regiones, archivo, indent=4)

    print("\nRegiones guardadas correctamente.")
    return regiones


def cargar_regiones():
    ruta = Path("datos/regiones.json")
    
    if not ruta.exists():
        print("El archivo de regiones no existe. Debes seleccionarlas primero.")
        return None

    with open(ruta, "r", encoding="utf-8") as archivo:
        regiones = json.load(archivo)
    
    return regiones


def dibujar_regiones(frame, regiones):
    """Dibuja los rectángulos de las zonas de espera y atención en el frame."""
    if not regiones:
        return frame

    colores = {
        "espera": (255, 165, 0),   # Naranja para espera
        "atencion": (0, 255, 0)    # Verde para atención
    }

    for clave, coords in regiones.items():
        x, y, ancho, alto = coords
        color = colores.get(clave, (255, 255, 255))
        
        cv2.rectangle(frame, (x, y), (x + ancho, y + alto), color, 2)
        
        texto = "ESPERA" if clave == "espera" else "ATENCION"
        cv2.putText(
            frame,
            texto,
            (x, max(y - 10, 20)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

    return frame


def obtener_zona(persona, regiones):
    """Determina si el centro inferior de la caja de la persona está dentro de alguna región."""
    if not regiones:
        return "fuera"

    x1, y1, x2, y2 = persona["caja"]
    centro_x = int((x1 + x2) / 2)
    punto_y = int(y2)

    for clave, coords in regiones.items():
        rx, ry, rancho, ralto = coords
        
        if rx <= centro_x <= (rx + rancho) and ry <= punto_y <= (ry + ralto):
            return clave

    return "fuera"