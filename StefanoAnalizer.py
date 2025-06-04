import pandas as pd
import requests
from bs4 import BeautifulSoup
from thefuzz import fuzz
from tqdm import tqdm
import time

def buscar_producto_stefano(nombre_producto):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://stefanocosmetics.com/search?q={nombre_producto}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}

    soup = BeautifulSoup(resp.text, 'html.parser')
    resultados = soup.select("a.full-unstyled-link")

    mejor_match = {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}

    for link in resultados:
        nombre_encontrado = link.get_text(strip=True)
        porcentaje = fuzz.partial_ratio(nombre_producto.lower(), nombre_encontrado.lower())

        if porcentaje >= 90 and porcentaje > mejor_match["coincidencia"]:
            url_producto = "https://stefanocosmetics.com" + link.get("href")
            resp_producto = requests.get(url_producto, headers=headers)
            soup_producto = BeautifulSoup(resp_producto.text, 'html.parser')
            precio_tag = soup_producto.select_one("span.price-item.price-item--regular")
            precio = precio_tag.get_text(strip=True) if precio_tag else "Precio no encontrado"

            mejor_match = {
                "nombre": nombre_encontrado,
                "precio": precio,
                "url": url_producto,
                "coincidencia": porcentaje
            }

    return mejor_match

# Leer archivo de Excel
df = pd.read_excel("nombres_stefano.xlsx")  # Asegúrate que la columna se llama 'nombre'
resultados = []

for nombre in tqdm(df["nombre"], desc="Procesando productos Stefano"):
    info = buscar_producto_stefano(str(nombre))
    info["nombre_buscado"] = nombre
    resultados.append(info)
    time.sleep(1)

# Guardar resultados
df_resultado = pd.DataFrame(resultados, columns=["nombre_buscado", "nombre", "coincidencia", "precio", "url"])
df_resultado.to_excel("productos_resultado_stefano.xlsx", index=False)

print("✅ Resultados guardados en productos_resultado_stefano.xlsx")
