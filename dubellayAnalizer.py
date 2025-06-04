import pandas as pd
import requests
import re
import json
from thefuzz import fuzz
from tqdm import tqdm
import time

# Palabras comunes que eliminamos para identificar palabras clave importantes
STOPWORDS = {
    "de", "la", "el", "y", "en", "los", "las", "un", "una", "paleta", "sombras",
    "sombra", "shadow", "palette", "makeup", "cosmetic", "cosmetics"
}

def extraer_keywords(texto):
    """Extrae palabras clave eliminando palabras comunes."""
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)  # quitar puntuación
    palabras = texto.split()
    return set(p for p in palabras if p not in STOPWORDS)

def buscar_producto_dubellay(nombre_producto):
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://dubellay.mx/search?q={nombre_producto}"
    resp = requests.get(url, headers=headers)

    with open(f"debug_dubellay_{nombre_producto.replace(' ', '_')}.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}

    match = re.search(r'search_submitted",\s*({.*?})\);', resp.text, re.DOTALL)
    if not match:
        return {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}

    try:
        data = json.loads(match.group(1))
        variantes = data["searchResult"]["productVariants"]
        keywords = extraer_keywords(nombre_producto)

        mejor = {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}
        for variante in variantes:
            nombre_encontrado = variante["product"]["title"]
            porcentaje = fuzz.partial_ratio(nombre_producto.lower(), nombre_encontrado.lower())
            encontrado_tokens = set(nombre_encontrado.lower().split())
            coincide_claves = keywords.issubset(encontrado_tokens)

            print(f"Buscando: {nombre_producto} - Encontrado: {nombre_encontrado}")
            print(f"Porcentaje: {porcentaje}, Claves: {keywords}, Coinciden: {coincide_claves}")

            if porcentaje >= 70 and coincide_claves and porcentaje > mejor["coincidencia"]:
                precio = f"${variante['price']['amount']:.2f} {variante['price']['currencyCode']}"
                url_producto = "https://dubellay.mx" + variante["product"]["url"]
                mejor.update({
                    "nombre": nombre_encontrado,
                    "precio": precio,
                    "url": url_producto,
                    "coincidencia": porcentaje
                })

        return mejor

    except Exception as e:
        return {"nombre": "Error JSON", "precio": "-", "url": "-", "coincidencia": 0}

# Leer archivo Excel
df = pd.read_excel("nombres_dubellay.xlsx")  # Asegúrate que la columna se llama 'nombre'
resultados = []

for nombre in tqdm(df["nombre"], desc="Procesando productos Dubellay"):
    info = buscar_producto_dubellay(str(nombre))
    info["nombre_buscado"] = nombre
    resultados.append(info)
    time.sleep(1)

# Guardar resultados
df_resultado = pd.DataFrame(resultados, columns=["nombre_buscado", "nombre", "coincidencia", "precio", "url"])
df_resultado.to_excel("productos_resultado_dubellay.xlsx", index=False)

print("✅ Resultados guardados en productos_resultado_dubellay.xlsx")
