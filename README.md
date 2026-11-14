# Monitoreo de Cafetería con Visión Artificial

Este proyecto utiliza Python, OpenCV y YOLO11 para analizar un video de una cafetería. Permite detectar y contar personas, medir cuánto tiempo esperan los clientes y cuánto dura su atención.

## 1. Requisitos

Para ejecutar el proyecto se necesita:

- Python 3.10 o una versión compatible con Ultralytics.
- Git.
- Las dependencias indicadas en `requirements.txt`.

## 2. Instalación

Los siguientes pasos se realizan desde PowerShell en Windows.

**Paso 1.** Descargar el repositorio:

```powershell
git clone https://github.com/estefww3-ux/Monitoreo_Cafeteria-.git
cd Monitoreo_Cafeteria-
```

**Paso 2.** Crear un entorno virtual:
```powershell
python -m venv venv
```

**Paso 3.** Activarlo:

```powershell
.\venv\Scripts\Activate.ps1
```

**Paso 4.** Instalar las dependencias:
```powershell
pip install -r requirements.txt
```

La instalación puede tardar algunos minutos debido a las librerías necesarias para trabajar con YOLO11.

## 3. Dependencias

Las principales librerías utilizadas en el proyecto son:

| Librería | Uso |
|---|---|
| `opencv-python` | Permite leer y procesar el video. |
| `ultralytics` | Se utiliza para realizar la detección de personas con YOLO11. |
| `numpy` | Ayuda con las operaciones sobre las imágenes. |
| `lap` | Se utiliza en el seguimiento de personas. |
| `pandas` | Permite apoyar el análisis de los archivos CSV. |

## 4. Ejecución del programa

Para iniciar el sistema, ejecutar:

```powershell
python main.py
```

Durante la reproducción del video se pueden utilizar las siguientes teclas:

| Tecla | Función |
|---|---|
| `P` | Pausar o continuar el video. |
| `R` | Configurar nuevamente las zonas ROI. |
| `Q` | Finalizar el programa y mostrar el resumen. |

## 5. Calibración de las regiones de interés (ROI)

Para que el sistema pueda diferenciar a los clientes que esperan de los que están siendo atendidos, es necesario configurar dos regiones dentro del video:

- **Zona de espera:** lugar donde los clientes forman la fila.
- **Zona de atención:** espacio frente al mostrador donde se atiende a los clientes.

La configuración se realiza de la siguiente manera:

1. Ejecutar el programa con `python main.py`.
2. Presionar `P` para pausar el video cuando se observe claramente el mostrador.
3. Presionar `R` para comenzar a configurar las regiones.
4. Dibujar con el mouse un rectángulo sobre el piso donde esperan los clientes y presionar `ENTER`.
5. Dibujar el segundo rectángulo en la zona donde se realiza la atención y presionar nuevamente `ENTER`.
6. Presionar `P` para continuar con el video.

Las regiones configuradas se guardan en el archivo `datos/regiones.json`, por lo que no es necesario dibujarlas nuevamente en cada ejecución si se mantiene el mismo video y encuadre.

**Recomendaciones:**

- Dibujar las regiones sobre el piso, donde se ubican los clientes.
- Evitar que las zonas se superpongan.
- No incluir el espacio donde trabajan los empleados.
- Volver a calibrar las regiones si se cambia el video, la posición de la cámara o el tamaño del fotograma.

## 6. Resultados

Al finalizar la ejecución, el sistema muestra un resumen de los tiempos de espera, atención y abandonos registrados.

Además, guarda los eventos en un archivo CSV dentro de la carpeta `resultados/`, para que la información pueda revisarse posteriormente.
