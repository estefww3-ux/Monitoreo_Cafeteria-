
import cv2

from deteccion.detector import DetectorPersonas


def main():

    # Crear el detector
    detector = DetectorPersonas()

    # Abrir la camara web
    camara = cv2.VideoCapture(0)

    if not camara.isOpened():
        print("Error: No se pudo abrir la camara")
        return

    print("Sistema de monitoreo iniciado")
    print("Presiona Q para salir")

    while True:

        # Capturar un fotograma
        ret, frame = camara.read()

        if not ret:
            print("No se pudo obtener el fotograma")
            break

        # Detectar personas
        detecciones = detector.detectar(frame)

        # Dibujar las detecciones
        frame = detector.dibujar(frame, detecciones)

        # Mostrar cantidad de personas detectadas
        cantidad = len(detecciones)

        cv2.putText(
            frame,
            f"Personas detectadas: {cantidad}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        # Mostrar video
        cv2.imshow("Monitoreo de Cafeteria", frame)

        # Salir al presionar Q
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Liberar recursos
    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
