
import csv
from datetime import datetime
from pathlib import Path


class Metricas:

    def __init__(self, ruta_csv=None):
        self.tiempos_espera = []     # esperas completadas (pasaron a atención)
        self.tiempos_atencion = []   # atenciones completadas
        self.tiempos_abandono = []   # esperas de quienes se fueron sin ser atendidos

        self.ruta_csv = Path(ruta_csv) if ruta_csv else None
        self._archivo = None
        self._escritor = None

        if self.ruta_csv:
            self._abrir_csv()

    # ------------------------------------------------------------------
    # Registro en CSV
    # ------------------------------------------------------------------
    def _abrir_csv(self):
        self.ruta_csv.parent.mkdir(parents=True, exist_ok=True)

        # utf-8-sig para que Excel muestre bien los acentos
        self._archivo = open(self.ruta_csv, "w", newline="", encoding="utf-8-sig")
        self._escritor = csv.writer(self._archivo)
        self._escritor.writerow(
            ["id", "evento", "duracion_seg", "momento_video_seg", "fecha_hora"]
        )
        self._archivo.flush()

    def _guardar_evento(self, identificador, evento, segundos, momento):
        if self._escritor is None:
            return

        self._escritor.writerow([
            identificador if identificador is not None else "",
            evento,
            f"{segundos:.2f}",
            f"{momento:.2f}" if momento is not None else "",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ])
        # flush en cada fila: si el programa se cierra de golpe, no se pierde nada
        self._archivo.flush()

    def cerrar(self):
        """Cierra el archivo CSV (llamar al terminar el programa)."""
        if self._archivo is not None:
            self._archivo.close()
            self._archivo = None
            self._escritor = None

    # ------------------------------------------------------------------
    # Registro de eventos
    # ------------------------------------------------------------------
    def registrar_espera(self, segundos, identificador=None, momento=None):
        self.tiempos_espera.append(segundos)
        self._guardar_evento(identificador, "espera_completada", segundos, momento)

    def registrar_atencion(self, segundos, identificador=None, momento=None):
        self.tiempos_atencion.append(segundos)
        self._guardar_evento(identificador, "atencion_completada", segundos, momento)

    def registrar_abandono(self, segundos, identificador=None, momento=None):
        self.tiempos_abandono.append(segundos)
        self._guardar_evento(identificador, "abandono", segundos, momento)

    # ------------------------------------------------------------------
    # Resumen
    # ------------------------------------------------------------------
    @staticmethod
    def _promedio(valores):
        return sum(valores) / len(valores) if valores else 0.0

    def obtener_resumen(self, personas_espera=0, personas_atencion=0,
                        esperas_actuales=None):
        """
        personas_espera / personas_atencion: clientes en cada zona ahora mismo.
        esperas_actuales: lista con los segundos que lleva esperando cada
                          cliente que sigue en la zona de espera.
        """
        esperas_actuales = esperas_actuales or []

        promedio_atencion = self._promedio(self.tiempos_atencion)

        # Estimación simple para un cliente que llegara ahora: debe esperar
        # a todos los que están por delante (en espera y en atención), y cada
        # uno tarda en promedio lo que dura una atención. Supone un solo
        # punto de atención. Sin atenciones completadas no hay base para estimar.
        if self.tiempos_atencion:
            por_delante = personas_espera + personas_atencion
            espera_estimada = promedio_atencion * por_delante
        else:
            espera_estimada = None

        return {
            "total_esperas": len(self.tiempos_espera),
            "total_atenciones": len(self.tiempos_atencion),
            "abandonos": len(self.tiempos_abandono),
            "promedio_espera": self._promedio(self.tiempos_espera),
            "promedio_atencion": promedio_atencion,
            "espera_maxima": max(self.tiempos_espera + esperas_actuales, default=0.0),
            "espera_estimada": espera_estimada,
        }
