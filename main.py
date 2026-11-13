
import time
from pathlib import Path

import cv2

from deteccion.detector import DetectorPersonas
from procesamiento.conteo import ContadorPersonas
from procesamiento.regiones import (
    seleccionar_regiones,
    cargar_regiones,
    dibujar_regiones,
    obtener_zona,
)
from servicios.cronometro import GestorTiempos
from servicios.metricas import Metricas
from interfaz.dashboard import dibujar_dashboard


# ----------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------
# Carpeta del proyecto: permite ejecutar desde cualquier ubicación
RAIZ = Path(__file__).resolve().parent

# Fuente de video: una ruta a un archivo, o 0 para usar la webcam
FUENTE = RAIZ / "datos" / "personas.mp4"

MODELO = RAIZ / "modelos" / "yolo11n.pt"
CONFIANZA = 0.5

# Segundos de espera a partir de los cuales se activa la alerta
LIMITE_ESPERA = 60

# True: el video vuelve a empezar al terminar. False: el programa termina.
REPETIR_VIDEO = True


def registrar_eventos(eventos, metricas, abandonos):
    """Guarda en las métricas los tiempos que se acaban de cerrar."""
    if eventos["espera_finalizada"] is not None:
        metricas.registrar_espera(eventos["espera_finalizada"])

    if eventos["atencion_finalizada"] is not None:
        metricas.registrar_atencion(eventos["atencion_finalizada"])

    if eventos["abandono"] is not None:
        abandonos.append(eventos["abandono"])


def crear_detector():
    return DetectorPersonas(modelo=str(MODELO), confianza=CONFIANZA)


def main():
    es_archivo = not isinstance(FUENTE, int)

    detector = crear_detector()
    contador = ContadorPersonas()
    cronometro = GestorTiempos()
    metricas = Metricas()
    abandonos = []  # tiempos de quienes se fueron sin ser atendidos

    camara = cv2.VideoCapture(str(FUENTE) if es_archivo else FUENTE)

    if not camara.isOpened():
        print(f"No se pudo abrir el video en la ruta: {FUENTE}")
        return

    correcto, primer_frame = camara.read()

    if not correcto:
        print("No se pudo leer el primer fotograma del video.")
        camara.release()
        return

    regiones = cargar_regiones()

    if regiones is None:
        regiones = seleccionar_regiones(primer_frame)

    # Manejo del tiempo:
    #  - Video: tiempo = número de fotograma / fps (igual en cualquier PC)
    #  - Webcam: tiempo real transcurrido
    fps = camara.get(cv2.CAP_PROP_FPS) if es_archivo else 0
    if es_archivo and not fps > 0:
        fps = 30.0  # valor de respaldo si el video no informa sus fps

    if es_archivo:
        # Volver al inicio para que el primer fotograma también se analice
        camara.set(cv2.CAP_PROP_POS_FRAMES, 0)

    indice_frame = 0
    tiempo_base = 0.0  # suma la duración de las vueltas anteriores del video
    inicio_real = time.time()
    ahora = 0.0

    print("Monitoreo iniciado.")
    print("Presiona Q para salir.")
    print("Presiona R para seleccionar nuevamente las regiones.")

    resumen = metricas.obtener_resumen()
    conteo = {"personas_actuales": 0, "total_personas": 0}

    while True:
        correcto, frame = camara.read()

        if not correcto:
            if not (es_archivo and REPETIR_VIDEO):
                break

            # Fin del video: se cierran los cronómetros pendientes para no
            # perder esos tiempos, y se reinicia el video y el seguimiento.
            tiempo_base += indice_frame / fps
            indice_frame = 0

            limite = tiempo_base + cronometro.tolerancia_ausencia
            for _, eventos in cronometro.cerrar_ausentes(set(), limite):
                registrar_eventos(eventos, metricas, abandonos)

            camara.set(cv2.CAP_PROP_POS_FRAMES, 0)
            detector = crear_detector()  # reinicia los IDs del seguimiento
            continue

        # Tiempo actual de este fotograma (en segundos)
        if es_archivo:
            ahora = tiempo_base + indice_frame / fps
        else:
            ahora = time.time() - inicio_real
        indice_frame += 1

        # Copia sin dibujos: se usa para recalibrar las zonas con la tecla R
        frame_limpio = frame.copy()

        detecciones = detector.detectar(frame)
        conteo = contador.actualizar(detecciones)

        personas_espera = 0
        personas_atencion = 0
        alertas = []
        ids_visibles = set()

        for persona in detecciones:
            identificador = persona["id"]

            if identificador is None:
                continue

            ids_visibles.add(identificador)
            zona = obtener_zona(persona, regiones)

            if zona == "espera":
                personas_espera += 1
            elif zona == "atencion":
                personas_atencion += 1

            tiempos = cronometro.actualizar(identificador, zona, ahora)
            registrar_eventos(tiempos["eventos"], metricas, abandonos)

            if tiempos["espera"] > LIMITE_ESPERA:
                alertas.append(identificador)

            # Etiqueta bajo la persona: zona y segundos acumulados
            if zona == "espera":
                texto_zona = f"ESPERA {tiempos['espera']:.0f}s"
            elif zona == "atencion":
                texto_zona = f"ATENCION {tiempos['atencion']:.0f}s"
            else:
                texto_zona = "FUERA"

            x1, y1, x2, y2 = persona["caja"]
            cv2.putText(
                frame,
                texto_zona,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                2,
            )

        # Cerrar a quienes dejaron de aparecer en el video
        for _, eventos in cronometro.cerrar_ausentes(ids_visibles, ahora):
            registrar_eventos(eventos, metricas, abandonos)

        resumen = metricas.obtener_resumen()

        # La zona de espera se pinta en rojo si alguien superó el límite
        zonas_en_alerta = {"espera"} if alertas else set()

        frame = detector.dibujar(frame, detecciones)
        frame = dibujar_regiones(frame, regiones, zonas_en_alerta)

        frame = dibujar_dashboard(
            frame,
            personas_espera,
            personas_atencion,
            resumen,
            alertas,
        )

        cv2.putText(
            frame,
            f"DETECTADAS: {conteo['personas_actuales']}",
            (25, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
        )

        cv2.putText(
            frame,
            f"TOTAL OBSERVADO: {conteo['total_personas']}",
            (25, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2,
        )

        cv2.imshow("Monitoreo de Cafeteria", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

        if tecla == ord("r"):
            regiones = seleccionar_regiones(frame_limpio)

    camara.release()
    cv2.destroyAllWindows()

    # Registrar los tiempos de quienes seguían en pantalla al terminar
    limite = ahora + cronometro.tolerancia_ausencia
    for _, eventos in cronometro.cerrar_ausentes(set(), limite):
        registrar_eventos(eventos, metricas, abandonos)

    resumen = metricas.obtener_resumen()

    print("\nRESUMEN FINAL")
    print("----------------------------")
    print(f"Total de personas observadas: {conteo['total_personas']}")
    print(f"Esperas registradas: {resumen['total_esperas']}")
    print(f"Espera promedio: {resumen['promedio_espera']:.2f} segundos")
    print(f"Atención promedio: {resumen['promedio_atencion']:.2f} segundos")
    print(f"Abandonos (se fueron sin ser atendidos): {len(abandonos)}")


if __name__ == "__main__":
    main()
