import cv2

from deteccion.detector import DetectorPersonas
from procesamiento.conteo import ContadorPersonas
from procesamiento.regiones import (
    seleccionar_regiones,
    cargar_regiones,
    dibujar_regiones,
    obtener_zona
)

from servicios.cronometro import GestorTiempos
from servicios.metricas import Metricas
from interfaz.dashboard import dibujar_dashboard


# Fuente configurada para el video de personas
FUENTE = "datos/personas.mp4" 

LIMITE_ESPERA = 60


def main():
    detector = DetectorPersonas(
        modelo="modelos/yolo11n.pt",
        confianza=0.5
    )

    contador = ContadorPersonas()
    cronometro = GestorTiempos()
    metricas = Metricas()

    camara = cv2.VideoCapture(FUENTE)

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

    print("Monitoreo iniciado.")
    print("Presiona Q para salir.")
    print("Presiona R para seleccionar nuevamente las regiones.")

    resumen = metricas.obtener_resumen()
    conteo = {
        "personas_actuales": 0,
        "total_personas": 0
    }

    while True:
        correcto, frame = camara.read()

        # Si el video termina, se reinicia automáticamente en bucle
        if not correcto:
            camara.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        detecciones = detector.detectar(frame)
        conteo = contador.actualizar(detecciones)

        personas_espera = 0
        personas_atencion = 0
        alertas = []

        for persona in detecciones:
            identificador = persona["id"]

            if identificador is None:
                continue

            zona = obtener_zona(persona, regiones)

            if zona == "espera":
                personas_espera += 1
            elif zona == "atencion":
                personas_atencion += 1

            tiempos = cronometro.actualizar(
                identificador, zona
            )

            eventos = tiempos["eventos"]

            if eventos["espera_finalizada"] is not None:
                metricas.registrar_espera(
                    eventos["espera_finalizada"]
                )

            if eventos["atencion_finalizada"] is not None:
                metricas.registrar_atencion(
                    eventos["atencion_finalizada"]
                )

            if tiempos["espera"] > LIMITE_ESPERA:
                alertas.append(identificador)

            x1, y1, x2, y2 = persona["caja"]

            if zona == "espera":
                texto_zona = "ESPERA"
            elif zona == "atencion":
                texto_zona = "ATENCION"
            else:
                texto_zona = "FUERA"

            cv2.putText(
                frame,
                texto_zona,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                2
            )

        resumen = metricas.obtener_resumen()

        frame = detector.dibujar(frame, detecciones)
        frame = dibujar_regiones(frame, regiones)

        frame = dibujar_dashboard(
            frame,
            personas_espera,
            personas_atencion,
            resumen,
            alertas
        )

        cv2.putText(
            frame,
            f"DETECTADAS: {conteo['personas_actuales']}",
            (25, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        cv2.putText(
            frame,
            f"TOTAL OBSERVADO: {conteo['total_personas']}",
            (25, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 255),
            2
        )

        cv2.imshow("Monitoreo de Cafeteria", frame)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

        if tecla == ord("r"):
            regiones = seleccionar_regiones(frame)

    camara.release()
    cv2.destroyAllWindows()

    print("\nRESUMEN FINAL")
    print("----------------------------")
    print(f"Total de personas observadas: {conteo['total_personas']}")
    print(f"Esperas registradas: {resumen['total_esperas']}")
    print(f"Espera promedio: {resumen['promedio_espera']:.2f} segundos")
    print(f"Atención promedio: {resumen['promedio_atencion']:.2f} segundos")


if __name__ == "__main__":
    main()