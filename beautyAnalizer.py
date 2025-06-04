import pandas as pd
import requests
import re
import json
import time
from tqdm import tqdm  # barra de progreso

def obtener_info_producto_por_sku(sku):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url_busqueda = f"https://beautycreationscosmetics.com.mx/search?q={sku}"
    response = requests.get(url_busqueda, headers=headers)

    if response.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}

    match = re.search(r'search_submitted",\s*({.*?})\);', response.text, re.DOTALL)
    if not match:
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}

    try:
        json_data = json.loads(match.group(1))
        producto = json_data["searchResult"]["productVariants"][0]

        nombre = producto["product"]["title"]
        precio = f"${producto['price']['amount']:.2f} MXN"
        url_producto = "https://beautycreationscosmetics.com.mx" + producto["product"]["url"]

        return {"nombre": nombre, "precio": precio, "url": url_producto}
    except Exception:
        return {"nombre": "Error JSON", "precio": "-", "url": "-"}

# Leer el archivo Excel
df_skus = pd.read_excel("skus.xlsx")  # Asegúrate que la columna se llama "SKU"

# Obtener información con barra de progreso
resultados = []
for sku in tqdm(df_skus["SKU"], desc="Procesando SKUs"):
    info = obtener_info_producto_por_sku(str(sku))
    info["SKU"] = sku
    resultados.append(info)
    time.sleep(1)

# Crear DataFrame y guardar en Excel
df_resultado = pd.DataFrame(resultados, columns=["SKU", "nombre", "precio", "url"])
df_resultado.to_excel("productos_resultado.xlsx", index=False)

print("✅ Consulta completada. Resultados guardados en productos_resultado.xlsx")
