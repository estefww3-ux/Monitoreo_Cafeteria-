
class SeguimientoPersonas:

    def __init__(self):

        # Conjunto de IDs observados
        self.ids_detectados = set()

    def actualizar(self, detecciones):

        # Obtener IDs visibles en este fotograma
        ids_actuales = {
            persona["id"]
            for persona in detecciones
            if persona["id"] is not None
        }

        # Registrar los IDs encontrados
        self.ids_detectados.update(ids_actuales)

        # Preparar resumen
        resumen = {
            "personas_actuales": len(ids_actuales),
            "total_ids_observados": len(self.ids_detectados),
            "ids_actuales": ids_actuales
        }

        return resumen
