

class GestorTiempos:

    def __init__(self, tolerancia_zona=1.5, tolerancia_ausencia=3.0):
        # Segundos en una zona nueva para confirmar el cambio
        self.tolerancia_zona = tolerancia_zona
        # Segundos sin verse para dar por terminada a una persona
        self.tolerancia_ausencia = tolerancia_ausencia
        # Estado de cada persona, indexado por su ID de seguimiento
        self.personas = {}

    # ------------------------------------------------------------------
    # Funciones internas
    # ------------------------------------------------------------------
    @staticmethod
    def _eventos_vacios():
        return {
            "espera_finalizada": None,    # pasó de espera a atención (segundos)
            "atencion_finalizada": None,  # terminó su atención (segundos)
            "abandono": None,             # dejó la espera sin ser atendida (segundos)
        }

    @staticmethod
    def _persona_nueva(ahora):
        return {
            "zona_actual": "fuera",       # zona confirmada
            "zona_candidata": None,       # zona nueva en período de prueba
            "candidata_desde": None,      # instante en que apareció en ella
            "inicio_espera": None,
            "inicio_atencion": None,
            "ultima_vez_visto": ahora,
        }

    def _cambiar_zona(self, persona, nueva, instante, eventos):
        """Cierra el cronómetro de la zona anterior y abre el de la nueva."""
        anterior = persona["zona_actual"]

        if anterior == "espera" and persona["inicio_espera"] is not None:
            duracion = instante - persona["inicio_espera"]
            if nueva == "atencion":
                eventos["espera_finalizada"] = duracion
            else:
                eventos["abandono"] = duracion
            persona["inicio_espera"] = None

        elif anterior == "atencion" and persona["inicio_atencion"] is not None:
            eventos["atencion_finalizada"] = instante - persona["inicio_atencion"]
            persona["inicio_atencion"] = None

        if nueva == "espera":
            persona["inicio_espera"] = instante
        elif nueva == "atencion":
            persona["inicio_atencion"] = instante

        persona["zona_actual"] = nueva

    # ------------------------------------------------------------------
    # Funciones públicas
    # ------------------------------------------------------------------
    def actualizar(self, identificador, zona, ahora):
        """
        Actualiza a una persona visible en este fotograma.

        identificador: ID del seguimiento (no debe ser None)
        zona:          "espera", "atencion" o "fuera"
        ahora:         tiempo actual en segundos (del video o time.time())

        Devuelve: {"espera": seg, "atencion": seg, "eventos": {...}}
        """
        if identificador not in self.personas:
            self.personas[identificador] = self._persona_nueva(ahora)

        persona = self.personas[identificador]
        persona["ultima_vez_visto"] = ahora
        eventos = self._eventos_vacios()

        if zona == persona["zona_actual"]:
            # Sigue donde estaba: se descarta cualquier cambio pendiente
            persona["zona_candidata"] = None

        elif persona["zona_candidata"] != zona:
            # Primera vez que se ve en una zona nueva: empieza el período de prueba
            persona["zona_candidata"] = zona
            persona["candidata_desde"] = ahora

        elif ahora - persona["candidata_desde"] >= self.tolerancia_zona:
            # Se mantuvo el tiempo suficiente: el cambio es real
            self._cambiar_zona(persona, zona, persona["candidata_desde"], eventos)
            persona["zona_candidata"] = None

        espera = 0
        if persona["inicio_espera"] is not None:
            espera = ahora - persona["inicio_espera"]

        atencion = 0
        if persona["inicio_atencion"] is not None:
            atencion = ahora - persona["inicio_atencion"]

        return {"espera": espera, "atencion": atencion, "eventos": eventos}

    def cerrar_ausentes(self, ids_visibles, ahora):
        """
        Cierra a las personas que dejaron de aparecer en el video.
        Debe llamarse una vez por fotograma, con los IDs visibles en ese momento.

        Devuelve una lista de (identificador, eventos) para registrar sus tiempos.
        """
        finalizados = []

        for identificador in list(self.personas):
            if identificador in ids_visibles:
                continue

            persona = self.personas[identificador]
            if ahora - persona["ultima_vez_visto"] < self.tolerancia_ausencia:
                continue

            # El tiempo termina en el último instante en que se la vio
            eventos = self._eventos_vacios()
            self._cambiar_zona(persona, "fuera", persona["ultima_vez_visto"], eventos)

            finalizados.append((identificador, eventos))
            del self.personas[identificador]

        return finalizados