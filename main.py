
import time
from datetime import datetime
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
FUENTE = RAIZ / "datos" / "personas_02.mp4"

MODELO = RAIZ / "modelos" / "yolo11n.pt"
CONFIANZA = 0.5

# Los fotogramas más anchos que esto se reducen (mantiene la proporción).
# Si cambias este valor, hay que recalibrar las zonas.
ANCHO_MAXIMO = 1280

# Segundos de espera a partir de los cuales se activa la alerta.
# 15 sirve para la demo; en un negocio real puede ser 60 o más.
LIMITE_ESPERA = 15

# True: el video vuelve a empezar al terminar. False: el programa termina.
REPETIR_VIDEO = True

FUENTE_TEXTO = cv2.FONT_HERSHEY_SIMPLEX
TEXTO_AYUDA = "P: pausa | R: zonas | Q: salir"


# ----------------------------------------------------------------------
# Funciones auxiliares
# ----------------------------------------------------------------------
def redimensionar(frame):
    """Reduce el fotograma si es más ancho que ANCHO_MAXIMO."""
    alto, ancho = frame.shape[:2]

    if ancho <= ANCHO_MAXIMO:
        return frame

    escala = ANCHO_MAXIMO / ancho
    return cv2.resize(
        frame,
        (ANCHO_MAXIMO, int(alto * escala)),
        interpolation=cv2.INTER_AREA,
    )


def crear_detector():
    return DetectorPersonas(modelo=str(MODELO), confianza=CONFIANZA)


def registrar_eventos(identificador, eventos, metricas, momento):
    """Guarda en las métricas (y en el CSV) los tiempos que se acaban de cerrar."""
    if eventos["espera_finalizada"] is not None:
        metricas.registrar_espera(eventos["espera_finalizada"], identificador, momento)

    if eventos["atencion_finalizada"] is not None:
        metricas.registrar_atencion(eventos["atencion_finalizada"], identificador, momento)

    if eventos["abandono"] is not None:
        metricas.registrar_abandono(eventos["abandono"], identificador, momento)


def dibujar_aviso(frame, texto):
    """Dibuja un mensaje con fondo oscuro, centrado en la parte inferior."""
    alto, ancho = frame.shape[:2]
    (w, h), _ = cv2.getTextSize(texto, FUENTE_TEXTO, 0.7, 2)
    x = (ancho - w) // 2
    y = alto - 30

    cv2.rectangle(frame, (x - 12, y - h - 12), (x + w + 12, y + 12), (30, 30, 30), -1)
    cv2.putText(frame, texto, (x, y), FUENTE_TEXTO, 0.7, (0, 255, 255), 2)


def mostrar_pausa(base):
    """Muestra la imagen congelada con el aviso de pausa."""
    vista = base.copy()
    dibujar_aviso(vista, "PAUSA  -  P: continuar | R: zonas | Q: salir")
    cv2.imshow("Monitoreo de Cafeteria", vista)


def recalibrar(frame_limpio, regiones):
    """Abre la calibración. Si el usuario cancela, se conservan las zonas actuales."""
    nuevas = seleccionar_regiones(frame_limpio)
    return nuevas if nuevas is not None else regiones


# ----------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------
def main():
    es_archivo = not isinstance(FUENTE, int)

    detector = crear_detector()
    contador = ContadorPersonas()
    cronometro = GestorTiempos()

    # Cada ejecución guarda sus eventos en un CSV con la fecha y hora de inicio
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    metricas = Metricas(ruta_csv=RAIZ / "resultados" / f"eventos_{marca}.csv")

    camara = cv2.VideoCapture(str(FUENTE) if es_archivo else FUENTE)

    if not camara.isOpened():
        print(f"No se pudo abrir el video en la ruta: {FUENTE}")
        metricas.cerrar()
        return

    correcto, primer_frame = camara.read()

    if not correcto:
        print("No se pudo leer el primer fotograma del video.")
        camara.release()
        metricas.cerrar()
        return

    primer_frame = redimensionar(primer_frame)

    regiones = cargar_regiones()

    if regiones is None:
        print("\nAún no hay zonas calibradas.")
        print("Pausa el video con P cuando se vea bien el mostrador,")
        print("y presiona R para dibujar las zonas.")

    # Manejo del tiempo:
    #  - Video: tiempo = número de fotograma / fps (igual en cualquier PC)
    #  - Webcam: tiempo real transcurrido, descontando las pausas
    fps = camara.get(cv2.CAP_PROP_FPS) if es_archivo else 0
    if es_archivo and not fps > 0:
        fps = 30.0  # valor de respaldo si el video no informa sus fps

    if es_archivo:
        # Volver al inicio para que el primer fotograma también se analice
        camara.set(cv2.CAP_PROP_POS_FRAMES, 0)

    indice_frame = 0
    tiempo_base = 0.0  # suma la duración de las vueltas anteriores del video
    inicio_real = time.time()
    tiempo_pausado = 0.0  # segundos detenidos (solo importa con webcam)
    inicio_pausa = 0.0
    ahora = 0.0

    en_pausa = False
    frame_limpio = primer_frame.copy()  # último fotograma sin dibujos
    ultimo_frame = primer_frame         # último fotograma mostrado

    print("\nMonitoreo iniciado.")
    print("P = pausar/continuar | R = seleccionar zonas | Q = salir")

    conteo = {"personas_actuales": 0, "total_personas": 0}

    while True:
        # --------------------------------------------------------------
        # Modo pausa: no se lee video, solo se esperan teclas
        # --------------------------------------------------------------
        if en_pausa:
            tecla = cv2.waitKey(50) & 0xFF

            if tecla == ord("q"):
                break

            if tecla == ord("p"):
                en_pausa = False
                tiempo_pausado += time.time() - inicio_pausa

            elif tecla == ord("r"):
                regiones = recalibrar(frame_limpio, regiones)
                ultimo_frame = dibujar_regiones(frame_limpio.copy(), regiones)
                mostrar_pausa(ultimo_frame)

            continue

        # --------------------------------------------------------------
        # Lectura del fotograma
        # --------------------------------------------------------------
        correcto, frame = camara.read()

        if not correcto:
            if not (es_archivo and REPETIR_VIDEO):
                break

            # Fin del video: se cierran los cronómetros pendientes para no
            # perder esos tiempos, y se reinicia el video y el seguimiento.
            tiempo_base += indice_frame / fps
            indice_frame = 0

            limite = tiempo_base + cronometro.tolerancia_ausencia
            for identificador, eventos in cronometro.cerrar_ausentes(set(), limite):
                registrar_eventos(identificador, eventos, metricas, tiempo_base)

            camara.set(cv2.CAP_PROP_POS_FRAMES, 0)
            detector = crear_detector()  # reinicia los IDs del seguimiento
            continue

        frame = redimensionar(frame)

        # Tiempo actual de este fotograma (en segundos)
        if es_archivo:
            ahora = tiempo_base + indice_frame / fps
        else:
            ahora = time.time() - inicio_real - tiempo_pausado
        indice_frame += 1

        # Copia sin dibujos: se usa para calibrar las zonas
        frame_limpio = frame.copy()

        # --------------------------------------------------------------
        # Detección y cronometraje
        # --------------------------------------------------------------
        detecciones = detector.detectar(frame)
        conteo = contador.actualizar(detecciones)

        personas_espera = 0
        personas_atencion = 0
        alertas = []
        esperas_actuales = []  # segundos que lleva esperando cada cliente en la fila
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
            registrar_eventos(identificador, tiempos["eventos"], metricas, ahora)

            if tiempos["espera"] > 0:
                esperas_actuales.append(tiempos["espera"])

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
                FUENTE_TEXTO,
                0.5,
                (255, 255, 0),
                2,
            )

        # Cerrar a quienes dejaron de aparecer en el video
        for identificador, eventos in cronometro.cerrar_ausentes(ids_visibles, ahora):
            registrar_eventos(identificador, eventos, metricas, ahora)

        resumen = metricas.obtener_resumen(
            personas_espera, personas_atencion, esperas_actuales
        )

        # --------------------------------------------------------------
        # Dibujo de la interfaz
        # --------------------------------------------------------------
        # La zona de espera se pinta en rojo si alguien superó el límite
        zonas_en_alerta = {"espera"} if alertas else set()

        frame = detector.dibujar(frame, detecciones)
        frame = dibujar_regiones(frame, regiones, zonas_en_alerta)

        frame = dibujar_dashboard(frame, {
            "personas_espera": personas_espera,
            "personas_atencion": personas_atencion,
            "personas_detectadas": conteo["personas_actuales"],
            "total_observado": conteo["total_personas"],
            "resumen": resumen,
            "alertas": alertas,
            "limite_espera": LIMITE_ESPERA,
        })

        # Recordatorio de teclas en la esquina inferior derecha
        (w_ayuda, _), _ = cv2.getTextSize(TEXTO_AYUDA, FUENTE_TEXTO, 0.5, 1)
        cv2.putText(
            frame,
            TEXTO_AYUDA,
            (frame.shape[1] - w_ayuda - 15, frame.shape[0] - 12),
            FUENTE_TEXTO,
            0.5,
            (255, 255, 255),
            1,
        )

        cv2.imshow("Monitoreo de Cafeteria", frame)
        ultimo_frame = frame

        # --------------------------------------------------------------
        # Teclas
        # --------------------------------------------------------------
        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("q"):
            break

        if tecla == ord("p"):
            en_pausa = True
            inicio_pausa = time.time()
            mostrar_pausa(ultimo_frame)

        elif tecla == ord("r"):
            inicio_calibracion = time.time()
            regiones = recalibrar(frame_limpio, regiones)
            tiempo_pausado += time.time() - inicio_calibracion

    camara.release()
    cv2.destroyAllWindows()

    # Registrar los tiempos de quienes seguían en pantalla al terminar
    limite = ahora + cronometro.tolerancia_ausencia
    for identificador, eventos in cronometro.cerrar_ausentes(set(), limite):
        registrar_eventos(identificador, eventos, metricas, ahora)

    resumen = metricas.obtener_resumen()
    metricas.cerrar()

    print("\nRESUMEN FINAL")
    print("----------------------------")
    print(f"Total de personas observadas: {conteo['total_personas']}")
    print(f"Esperas completadas: {resumen['total_esperas']}")
    print(f"Espera promedio: {resumen['promedio_espera']:.2f} segundos")
    print(f"Espera máxima: {resumen['espera_maxima']:.2f} segundos")
    print(f"Atenciones completadas: {resumen['total_atenciones']}")
    print(f"Atención promedio: {resumen['promedio_atencion']:.2f} segundos")
    print(f"Abandonos (se fueron sin ser atendidos): {resumen['abandonos']}")
    print(f"Eventos guardados en: {metricas.ruta_csv}")


if __name__ == "__main__":
    main()
