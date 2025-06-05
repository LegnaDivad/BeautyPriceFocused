import requests
import re
import json
import time
from typing import Optional
from bs4 import BeautifulSoup


def search_beautycreations_sku(sku: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Beauty Creations por SKU."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://beautycreationscosmetics.com.mx/search?q={sku}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}

    match = re.search(r'search_submitted",\s*({.*?})\);', resp.text, re.DOTALL)
    if not match:
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}
    try:
        data = json.loads(match.group(1))
        variante = data["searchResult"]["productVariants"][0]
        nombre = variante["product"]["title"]
        precio = f"${variante['price']['amount']:.2f} MXN"
        url_producto = "https://beautycreationscosmetics.com.mx" + variante["product"]["url"]
        return {"nombre": nombre, "precio": precio, "url": url_producto}
    except Exception:
        return {"nombre": "Error JSON", "precio": "-", "url": "-"}


def search_bellisima_sku(sku: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Bellisima por SKU."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://bellisima.mx/search?q={sku}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    soup = BeautifulSoup(resp.text, "html.parser")
    enlace = soup.select_one("a.product-item-meta__title")
    if not enlace:
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}
    nombre = enlace.get_text(strip=True)
    url_producto = "https://bellisima.mx" + enlace["href"]
    precio_tag = soup.select_one("span.price.price--highlight")
    precio = precio_tag.get_text(strip=True) if precio_tag else "No disponible"
    precio = precio.replace("Precio de venta", "").replace(" ", "").replace("$", "")
    return {"nombre": nombre, "precio": precio, "url": url_producto}


def search_stefano_name(nombre_producto: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Stefano por nombre."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://stefanocosmetics.com/search?q={nombre_producto}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = soup.select("a.full-unstyled-link")
    mejor = {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}
    for link in resultados:
        nombre_encontrado = link.get_text(strip=True)
        # simple ratio using Python's SequenceMatcher
        from difflib import SequenceMatcher
        porcentaje = int(SequenceMatcher(None, nombre_producto.lower(), nombre_encontrado.lower()).ratio()*100)
        if porcentaje >= 90 and porcentaje > mejor["coincidencia"]:
            url_producto = "https://stefanocosmetics.com" + link.get("href")
            try:
                resp_producto = session.get(url_producto, headers=headers, timeout=10)
                time.sleep(1)
            except requests.RequestException:
                continue
            soup_prod = BeautifulSoup(resp_producto.text, "html.parser")
            precio_tag = soup_prod.select_one("span.price-item.price-item--regular")
            precio = precio_tag.get_text(strip=True) if precio_tag else "Precio no encontrado"
            mejor = {"nombre": nombre_encontrado, "precio": precio, "url": url_producto, "coincidencia": porcentaje}
    return mejor


def search_dubellay_name(nombre_producto: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Dubellay por nombre."""
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://dubellay.mx/search?q={nombre_producto}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    if resp.status_code != 200:
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    match = re.search(r'search_submitted",\s*({.*?})\);', resp.text, re.DOTALL)
    if not match:
        return {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}
    try:
        data = json.loads(match.group(1))
        variantes = data["searchResult"]["productVariants"]
        mejor = {"nombre": "No encontrado", "precio": "-", "url": "-", "coincidencia": 0}
        for var in variantes:
            nombre_encontrado = var["product"]["title"]
            from difflib import SequenceMatcher
            porcentaje = int(SequenceMatcher(None, nombre_producto.lower(), nombre_encontrado.lower()).ratio()*100)
            if porcentaje >= 70 and porcentaje > mejor["coincidencia"]:
                precio = f"${var['price']['amount']:.2f} {var['price']['currencyCode']}"
                url_producto = "https://dubellay.mx" + var["product"]["url"]
                mejor = {"nombre": nombre_encontrado, "precio": precio, "url": url_producto, "coincidencia": porcentaje}
        return mejor
    except Exception:
        return {"nombre": "Error JSON", "precio": "-", "url": "-", "coincidencia": 0}
