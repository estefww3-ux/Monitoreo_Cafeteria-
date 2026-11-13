
import cv2
from ultralytics import YOLO


class DetectorPersonas:

    def __init__(self, modelo="yolo11n.pt", confianza=0.5):

        # Cargar el modelo YOLO
        self.modelo = YOLO(modelo)

        self.confianza = confianza

    def detectar(self, frame):

        # Detectar y seguir personas
        resultados = self.modelo.track(
            source=frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=self.confianza,
            classes=[0],
            verbose=False
        )

        detecciones = []

        # Obtener las cajas detectadas
        cajas = resultados[0].boxes

        # Obtener los identificadores
        if cajas.id is not None:
            identificadores = cajas.id.int().cpu().tolist()
        else:
            identificadores = [None] * len(cajas)

        for caja, identificador in zip(cajas, identificadores):

            # Obtener coordenadas
            coordenadas = (
                caja.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )

            x1, y1, x2, y2 = coordenadas

            # Obtener confianza
            confianza = float(caja.conf[0].cpu())

            persona = {
                "id": identificador,
                "caja": (x1, y1, x2, y2),
                "confianza": confianza
            }

            detecciones.append(persona)

        return detecciones

    def dibujar(self, frame, detecciones):

        for persona in detecciones:

            x1, y1, x2, y2 = persona["caja"]

            identificador = persona["id"]
            confianza = persona["confianza"]

            # Dibujar rectangulo
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Preparar etiqueta
            if identificador is not None:
                texto = f"ID: {identificador} | {confianza:.2f}"
            else:
                texto = f"Persona | {confianza:.2f}"

            cv2.putText(
                frame,
                texto,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

        return frame
