
import cv2


def dibujar_dashboard(frame, personas_espera, personas_atencion,
                      resumen, alertas):

    alto, ancho = frame.shape[:2]

    # Panel de información
    cv2.rectangle(
        frame, (10, 10), (ancho - 10, 155),
        (30, 30, 30), -1
    )

    textos = [
        f"PERSONAS EN ESPERA: {personas_espera}",
        f"PERSONAS EN ATENCION: {personas_atencion}",
        f"ESPERA PROMEDIO: {resumen['promedio_espera']:.1f} seg",
        f"ATENCION PROMEDIO: {resumen['promedio_atencion']:.1f} seg"
    ]

    y = 40

    for texto in textos:
        cv2.putText(
            frame, texto, (25, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (255, 255, 255), 2
        )
        y += 28

    # Alertas de espera prolongada
    if alertas:
        mensaje = "ALERTA: ESPERA PROLONGADA"
        cv2.putText(
            frame, mensaje, (25, alto - 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            (0, 0, 255), 2
        )

    return frame
