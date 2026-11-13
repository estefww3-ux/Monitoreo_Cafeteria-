
class Metricas:
    def __init__(self):
        self.tiempos_espera = []
        self.tiempos_atencion = []

    def registrar_espera(self, segundos):
        self.tiempos_espera.append(segundos)

    def registrar_atencion(self, segundos):
        self.tiempos_atencion.append(segundos)

    def obtener_resumen(self):
        promedio_espera = (
            sum(self.tiempos_espera) / len(self.tiempos_espera)
            if self.tiempos_espera else 0
        )

        promedio_atencion = (
            sum(self.tiempos_atencion) / len(self.tiempos_atencion)
            if self.tiempos_atencion else 0
        )

        return {
            "total_esperas": len(self.tiempos_espera),
            "promedio_espera": promedio_espera,
            "promedio_atencion": promedio_atencion
        }
    