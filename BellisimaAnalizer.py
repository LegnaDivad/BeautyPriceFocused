import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import json
import re

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

    # Consultar la página del producto para obtener el precio real
    resp_prod = requests.get(url_producto, headers=headers)
    soup_prod = BeautifulSoup(resp_prod.text, "html.parser")

    precio = None
    # bellisima renders the price in a couple of different markup variants
    # depending on the product state (on sale, regular, etc.).
    # Try several possible selectors before falling back to JSON/iframe parsing.
    precio_tag = (
        soup_prod.select_one("div.price-list span.price")
        or soup_prod.select_one("span.price.price--large")
        or soup_prod.select_one("span.price-item--regular")
        or soup_prod.select_one("span.price.price--highlight")
        or soup_prod.select_one("span.price__regular")
    )
    if precio_tag:
        text = precio_tag.get_text(" ", strip=True)
        m = re.search(r"\$\s*([0-9.,]+)", text)
        precio = m.group(1) if m else text

    if not precio:
        for script in soup_prod.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except Exception:
                continue
            if isinstance(data, dict) and data.get("@type") == "Product":
                offers = data.get("offers")
                if isinstance(offers, dict) and offers.get("price"):
                    precio = str(offers.get("price"))
                    break
            elif isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and d.get("@type") == "Product":
                        offers = d.get("offers")
                        if isinstance(offers, dict) and offers.get("price"):
                            precio = str(offers.get("price"))
                            break
                if precio:
                    break

    if not precio:
        iframe = soup_prod.find("iframe")
        if iframe and iframe.get("src"):
            resp_iframe = requests.get(iframe["src"], headers=headers)
            soup_iframe = BeautifulSoup(resp_iframe.text, "html.parser")
            m = re.search(r"\$\s*([0-9]+[.,]?[0-9]*)", soup_iframe.get_text(" ", strip=True))
            if m:
                precio = m.group(1)

    if not precio:
        precio = "No disponible"
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
