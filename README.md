# Beauty Price Focused

Esta aplicación permite consultar precios de productos de distintas tiendas de belleza a partir de archivos masivos o búsquedas individuales.

## Requisitos

Instala las dependencias (necesitas `requests` y otras librerías):

```bash
pip install -r requirements.txt
```

## Ejecución de la interfaz

Ejecuta la aplicación con Streamlit:

```bash
streamlit run app.py
```

Se abrirá una interfaz web donde podrás cargar un archivo con SKUs o nombres y realizar búsquedas individuales. Los resultados obtenidos se muestran en pantalla y se pueden descargar en Excel.

Todas las búsquedas se registran en `scraper.log`, lo que facilita detectar códigos de error como 403.
