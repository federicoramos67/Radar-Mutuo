"""Lectura de feeds RSS y Atom usando solo la biblioteca estándar de Python."""

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

AGENTE = "Mozilla/5.0 (compatible; RadarMutuo/1.0; +https://github.com/federicoramos67/radar-mutuo)"
_ETIQUETAS = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")


def limpiar_texto(texto, largo=600):
    """Saca HTML y espacios de más, y corta en un largo razonable."""
    if not texto:
        return ""
    texto = html.unescape(_ETIQUETAS.sub(" ", texto))
    texto = _ESPACIOS.sub(" ", texto).strip()
    if len(texto) > largo:
        texto = texto[:largo].rsplit(" ", 1)[0] + "…"
    return texto


def _fecha(texto):
    if not texto:
        return None
    texto = texto.strip()
    try:
        fecha = parsedate_to_datetime(texto)  # formato RSS
    except (TypeError, ValueError, IndexError):
        try:
            fecha = datetime.fromisoformat(texto.replace("Z", "+00:00"))  # formato Atom
        except ValueError:
            return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def _local(etiqueta):
    """Nombre de la etiqueta sin el espacio de nombres XML."""
    return etiqueta.rsplit("}", 1)[-1].lower()


def _hijo(nodo, *nombres):
    for h in nodo:
        if _local(h.tag) in nombres:
            return h
    return None


def _texto_hijo(nodo, *nombres):
    h = _hijo(nodo, *nombres)
    return (h.text or "").strip() if h is not None else ""


def parsear(xml_bytes, fuente):
    """Convierte un feed en una lista de items con el mismo formato."""
    raiz = ET.fromstring(xml_bytes)
    nodos = [n for n in raiz.iter() if _local(n.tag) in ("item", "entry")]
    items = []
    for n in nodos:
        titulo = limpiar_texto(_texto_hijo(n, "title"), 300)
        link = _texto_hijo(n, "link")
        if not link:
            for h in n:
                if _local(h.tag) == "link" and h.get("href"):
                    if h.get("rel", "alternate") == "alternate":
                        link = h.get("href")
                        break
        if not link:
            link = _texto_hijo(n, "guid", "id")
        resumen = _texto_hijo(n, "description", "summary", "content", "encoded")
        fecha = _fecha(_texto_hijo(n, "pubdate", "published", "updated", "date"))
        if not titulo or not link.startswith("http"):
            continue
        items.append(
            {
                "titulo": titulo,
                "link": link.strip(),
                "resumen": limpiar_texto(resumen),
                "fecha": fecha,
                "fuente": fuente["nombre"],
                "tipo": fuente["tipo"],
            }
        )
    return items


def descargar(url, timeout=20):
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(pedido, timeout=timeout) as r:
        return r.read()


def leer_todas(fuentes, descargador=descargar):
    """Lee todas las fuentes. Una fuente caída no frena a las demás.

    Devuelve (items, estado) donde estado dice qué fuentes respondieron.
    """
    items, estado = [], []
    for f in fuentes:
        try:
            nuevos = parsear(descargador(f["url"]), f)
            items.extend(nuevos)
            estado.append({"nombre": f["nombre"], "tipo": f["tipo"], "ok": True, "items": len(nuevos)})
        except Exception as e:  # red, XML roto, 404: se registra y se sigue
            estado.append({"nombre": f["nombre"], "tipo": f["tipo"], "ok": False, "error": type(e).__name__})
    return items, estado
