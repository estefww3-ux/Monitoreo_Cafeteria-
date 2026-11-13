
import cv2
from ultralytics import YOLO


class DetectorPersonas:

    def __init__(self, modelo="yolo11n.pt", confianza=0.5):

        # Cargar el modelo de inteligencia artificial
        self.modelo = YOLO(modelo)

        # Nivel minimo de confianza
        self.confianza = confianza

    def detectar(self, frame):

        # Enviar el fotograma al modelo YOLO
        resultados = self.modelo.predict(
            source=frame,
            conf=self.confianza,
            classes=[0],
            verbose=False
        )

        detecciones = []

        # Obtener las personas detectadas
        cajas = resultados[0].boxes

        for caja in cajas:

            # Coordenadas del rectangulo
            x1, y1, x2, y2 = caja.xyxy[0].cpu().numpy().astype(int)

            # Nivel de confianza de la deteccion
            confianza = float(caja.conf[0].cpu().numpy())

            # Guardar la informacion
            persona = {
                "caja": (x1, y1, x2, y2),
                "confianza": confianza
            }

            detecciones.append(persona)

        return detecciones

    def dibujar(self, frame, detecciones):

        # Recorrer las personas detectadas
        for persona in detecciones:

            x1, y1, x2, y2 = persona["caja"]
            confianza = persona["confianza"]

            # Dibujar rectangulo
            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Mostrar etiqueta
            texto = f"Persona: {confianza:.2f}"

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
