import requests
import re
import json
import time
import logging
from typing import Optional
from bs4 import BeautifulSoup

# Encabezados que simulan un navegador real para evitar bloqueos
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        "image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://google.com/",
}


logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def search_beautycreations_sku(sku: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Beauty Creations por SKU."""
    logger.info("Buscando SKU %s en Beauty Creations", sku)
    headers = DEFAULT_HEADERS
    url = f"https://beautycreationscosmetics.com.mx/search?q={sku}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException as e:
        logger.error("Error de conexión en Beauty Creations para %s: %s", sku, e)
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    if resp.status_code == 403:
        logger.error("Acceso denegado con código 403 en Beauty Creations para %s", sku)
        return {"nombre": "Acceso denegado", "precio": "-", "url": "-"}
    if resp.status_code != 200:
        logger.error("Código de respuesta %s en Beauty Creations para %s", resp.status_code, sku)
        return {"nombre": "Error", "precio": "Error", "url": "Error"}

    match = re.search(r'search_submitted",\s*({.*?})\);', resp.text, re.DOTALL)
    if not match:
        logger.info("SKU %s no encontrado en Beauty Creations", sku)
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}
    try:
        data = json.loads(match.group(1))
        variante = data["searchResult"]["productVariants"][0]
        nombre = variante["product"]["title"]
        precio = f"${variante['price']['amount']:.2f} MXN"
        url_producto = "https://beautycreationscosmetics.com.mx" + variante["product"]["url"]
        return {"nombre": nombre, "precio": precio, "url": url_producto}
    except Exception as e:
        logger.error("Error procesando JSON de Beauty Creations para %s: %s", sku, e)
        return {"nombre": "Error JSON", "precio": "-", "url": "-"}


def search_bellisima_sku(sku: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Bellisima por SKU."""
    logger.info("Buscando SKU %s en Bellisima", sku)
    headers = DEFAULT_HEADERS
    url = f"https://bellisima.mx/search?q={sku}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException as e:
        logger.error("Error de conexión en Bellisima para %s: %s", sku, e)
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    if resp.status_code == 403:
        logger.error("Acceso denegado con código 403 en Bellisima para %s", sku)
        return {"nombre": "Acceso denegado", "precio": "-", "url": "-"}
    if resp.status_code != 200:
        logger.error("Código de respuesta %s en Bellisima para %s", resp.status_code, sku)
        return {"nombre": "Error", "precio": "Error", "url": "Error"}
    soup = BeautifulSoup(resp.text, "html.parser")
    enlace = soup.select_one("a.product-item-meta__title")
    if not enlace:
        logger.info("SKU %s no encontrado en Bellisima", sku)
        return {"nombre": "No encontrado", "precio": "-", "url": "-"}
    nombre = enlace.get_text(strip=True)
    url_producto = "https://bellisima.mx" + enlace["href"]

    # Consultar la página del producto para obtener el precio real
    try:
        resp_prod = session.get(url_producto, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException as e:
        logger.error("Error obteniendo detalle en Bellisima para %s: %s", sku, e)
        return {"nombre": nombre, "precio": "Error", "url": url_producto}
    soup_prod = BeautifulSoup(resp_prod.text, "html.parser")
    precio: Optional[str] = None

    # Intentar extraer el precio de elementos visibles
    precio_tag = (
        soup_prod.select_one("div.price-list span.price")
        or soup_prod.select_one("span.price-item--regular")
        or soup_prod.select_one("span.price.price--highlight")
    )
    if precio_tag:
        text = precio_tag.get_text(" ", strip=True)
        m = re.search(r"\$\s*([0-9.,]+)", text)
        precio = m.group(1) if m else text

    # Intentar extraer el precio desde etiquetas JSON-LD
    if not precio:
        for script in soup_prod.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
            except Exception:
                continue
            if isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and d.get("@type") == "Product":
                        offers = d.get("offers")
                        if isinstance(offers, dict) and offers.get("price"):
                            precio = str(offers.get("price"))
                            break
                if precio:
                    break
            elif isinstance(data, dict) and data.get("@type") == "Product":
                offers = data.get("offers")
                if isinstance(offers, dict) and offers.get("price"):
                    precio = str(offers.get("price"))
                    break

    # Buscar dentro de un iframe como último recurso
    if not precio:
        iframe = soup_prod.find("iframe")
        if iframe and iframe.get("src"):
            try:
                resp_iframe = session.get(iframe["src"], headers=headers, timeout=10)
                time.sleep(1)
                soup_iframe = BeautifulSoup(resp_iframe.text, "html.parser")
                text = soup_iframe.get_text(" ", strip=True)
                m = re.search(r"\$\s*([0-9]+[.,]?[0-9]*)", text)
                if m:
                    precio = m.group(1)
            except requests.RequestException as e:
                logger.error("Error obteniendo iframe en Bellisima para %s: %s", sku, e)

    if not precio:
        precio = "No disponible"

    precio = precio.replace("Precio de venta", "").replace(" ", "").replace("$", "")
    return {"nombre": nombre, "precio": precio, "url": url_producto}


def search_stefano_name(nombre_producto: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Stefano por nombre."""
    logger.info("Buscando producto '%s' en Stefano", nombre_producto)
    headers = DEFAULT_HEADERS
    url = f"https://stefanocosmetics.com/search?q={nombre_producto}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException as e:
        logger.error("Error de conexión en Stefano para '%s': %s", nombre_producto, e)
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    if resp.status_code == 403:
        logger.error("Acceso denegado con código 403 en Stefano para '%s'", nombre_producto)
        return {"nombre": "Acceso denegado", "precio": "-", "url": "-", "coincidencia": 0}
    if resp.status_code != 200:
        logger.error("Código de respuesta %s en Stefano para '%s'", resp.status_code, nombre_producto)
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
            except requests.RequestException as e:
                logger.error("Error obteniendo detalle en Stefano para '%s': %s", nombre_encontrado, e)
                continue
            soup_prod = BeautifulSoup(resp_producto.text, "html.parser")
            precio_tag = soup_prod.select_one("span.price-item.price-item--regular")
            precio = precio_tag.get_text(strip=True) if precio_tag else "Precio no encontrado"
            mejor = {"nombre": nombre_encontrado, "precio": precio, "url": url_producto, "coincidencia": porcentaje}
    if mejor["coincidencia"] == 0:
        logger.info("Producto '%s' no encontrado en Stefano", nombre_producto)
    return mejor


def search_dubellay_name(nombre_producto: str, session: Optional[requests.Session] = None) -> dict:
    """Busca un producto en Dubellay por nombre."""
    logger.info("Buscando producto '%s' en Dubellay", nombre_producto)
    headers = DEFAULT_HEADERS
    url = f"https://dubellay.mx/search?q={nombre_producto}"
    session = session or requests.Session()
    try:
        resp = session.get(url, headers=headers, timeout=10)
        time.sleep(1)
    except requests.RequestException as e:
        logger.error("Error de conexión en Dubellay para '%s': %s", nombre_producto, e)
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    if resp.status_code == 403:
        logger.error("Acceso denegado con código 403 en Dubellay para '%s'", nombre_producto)
        return {"nombre": "Acceso denegado", "precio": "-", "url": "-", "coincidencia": 0}
    if resp.status_code != 200:
        logger.error("Código de respuesta %s en Dubellay para '%s'", resp.status_code, nombre_producto)
        return {"nombre": "Error", "precio": "Error", "url": "Error", "coincidencia": 0}
    match = re.search(r'search_submitted",\s*({.*?})\);', resp.text, re.DOTALL)
    if not match:
        logger.info("Producto '%s' no encontrado en Dubellay", nombre_producto)
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
        if mejor["coincidencia"] == 0:
            logger.info("Producto '%s' no encontrado en Dubellay", nombre_producto)
        return mejor
    except Exception as e:
        logger.error("Error procesando JSON de Dubellay para '%s': %s", nombre_producto, e)
        return {"nombre": "Error JSON", "precio": "-", "url": "-", "coincidencia": 0}
