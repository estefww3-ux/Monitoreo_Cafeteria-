
import time


class GestorTiempos:
    def __init__(self):
        self.personas = {}

    def actualizar(self, identificador, zona):
        ahora = time.time()

        if identificador not in self.personas:
            self.personas[identificador] = {
                "zona_anterior": "fuera",
                "inicio_espera": None,
                "inicio_atencion": None
            }

        persona = self.personas[identificador]
        zona_anterior = persona["zona_anterior"]

        eventos = {
            "espera_finalizada": None,
            "atencion_finalizada": None
        }

        if zona == "espera" and zona_anterior != "espera":
            persona["inicio_espera"] = ahora

        if zona == "atencion":
            if persona["inicio_espera"] is not None:
                eventos["espera_finalizada"] = (
                    ahora - persona["inicio_espera"]
                )
                persona["inicio_espera"] = None

            if persona["inicio_atencion"] is None:
                persona["inicio_atencion"] = ahora

        if zona == "fuera":
            if zona_anterior == "espera":
                persona["inicio_espera"] = None

            if zona_anterior == "atencion":
                if persona["inicio_atencion"] is not None:
                    eventos["atencion_finalizada"] = (
                        ahora - persona["inicio_atencion"]
                    )
                    persona["inicio_atencion"] = None

        persona["zona_anterior"] = zona

        espera_actual = 0
        atencion_actual = 0

        if persona["inicio_espera"] is not None:
            espera_actual = ahora - persona["inicio_espera"]

        if persona["inicio_atencion"] is not None:
            atencion_actual = ahora - persona["inicio_atencion"]

        return {
            "espera": espera_actual,
            "atencion": atencion_actual,
            "eventos": eventos
        }
