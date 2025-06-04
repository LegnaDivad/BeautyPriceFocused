import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time

def obtener_info_producto_bellisima(sku):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://bellisima.mx/search?q={sku}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Buscar nombre del producto y URL
    enlace = soup.select_one("a.product-item-meta__title")
    if not enlace:
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}

    nombre = enlace.get_text(strip=True)
    url_producto = "https://bellisima.mx" + enlace['href']

    # Extraer precio de venta actual
    precio_tag = soup.select_one("span.price.price--highlight")
    print(precio_tag)
    precio = precio_tag.get_text(strip=True) if precio_tag else "No disponible"
    precio = precio.replace("Precio de venta", "").replace(" ", "").replace("$", "")

    return {
        "nombre": nombre,
        "precio": precio,
        "url": url_producto
    }

# Leer archivo Excel con SKUs
df_skus = pd.read_excel("skus.xlsx")

# Ejecutar scraping con barra de carga
resultados = []
for sku in tqdm(df_skus["SKU"], desc="Procesando SKUs Bellisima"):
    info = obtener_info_producto_bellisima(str(sku))
    info["SKU"] = sku
    resultados.append(info)
    time.sleep(1)

# Guardar resultados en Excel
df_resultado = pd.DataFrame(resultados, columns=["SKU", "nombre", "precio", "url"])
df_resultado.to_excel("productos_resultado_bellisima.xlsx", index=False)

print("✅ Resultados guardados en productos_resultado_bellisima.xlsx")
