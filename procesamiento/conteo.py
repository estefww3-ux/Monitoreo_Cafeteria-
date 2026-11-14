class ContadorPersonas:
    """Cuenta las personas visibles ahora y las distintas vistas en total (por ID)."""

    def __init__(self):
        self.ids_observados = set()

    def actualizar(self, detecciones):
        ids_actuales = {
            persona["id"]
            for persona in detecciones
            if persona["id"] is not None
        }

        self.ids_observados.update(ids_actuales)

        return {
            "personas_actuales": len(ids_actuales),
            "total_personas": len(self.ids_observados),
        }