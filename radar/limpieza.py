"""Filtrado por fecha, deduplicación y agrupación de items que cuentan la misma historia."""

import re
import unicodedata
from datetime import timedelta
from urllib.parse import urlsplit, urlunsplit

PALABRAS_VACIAS = set(
    """a al and are as at be by de del el en es for from has how in is it its la las los
    new now of on or que se the to un una with y you your why what will this that just
    says said can more about after over into ai ia""".split()
)
# Términos de IA que aparecen en casi todo: no sirven para distinguir historias.
GENERICAS = {"model", "models", "modelo", "modelos", "artificial", "intelligence", "inteligencia", "launch", "launches", "announces", "update"}


def normalizar_url(url):
    p = urlsplit(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    ruta = p.path.rstrip("/")
    return urlunsplit((p.scheme.lower(), host, ruta, "", ""))


def dominio(url):
    host = urlsplit(url).netloc.lower().removeprefix("www.")
    partes = host.split(".")
    return ".".join(partes[-2:]) if len(partes) >= 2 else host


def palabras(titulo):
    t = unicodedata.normalize("NFKD", titulo.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    tokens = re.findall(r"[a-z0-9][a-z0-9.\-]*[a-z0-9]|[a-z0-9]", t)
    return {w for w in tokens if w not in PALABRAS_VACIAS and w not in GENERICAS and len(w) > 2}


def similitud(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def habla_de_ia(item, palabras_ia):
    plano = unicodedata.normalize("NFKD", (item["titulo"] + " " + item["resumen"]).lower())
    plano = " " + "".join(ch for ch in plano if not unicodedata.combining(ch)) + " "
    plano = re.sub(r"[^a-z0-9]+", " ", plano)
    for p in palabras_ia:
        q = unicodedata.normalize("NFKD", p.lower())
        q = "".join(ch for ch in q if not unicodedata.combining(ch))
        if f" {q} " in plano:
            return True
    return False


def filtrar_tema(items, fuentes, palabras_ia):
    generales = {f["nombre"] for f in fuentes if f.get("solo_ia")}
    return [i for i in items if i["fuente"] not in generales or habla_de_ia(i, palabras_ia)]


def filtrar_por_fecha(items, ahora, horas):
    limite = ahora - timedelta(hours=horas)
    # Un item sin fecha se acepta: muchas fuentes oficiales la omiten.
    return [i for i in items if i["fecha"] is None or i["fecha"] >= limite]


def deduplicar(items):
    vistos, salida = set(), []
    for i in items:
        clave = normalizar_url(i["link"])
        if clave in vistos:
            continue
        vistos.add(clave)
        salida.append(i)
    return salida


def agrupar(items, umbral=0.34):
    """Junta items de distintas fuentes que hablan de lo mismo.

    Cada grupo es una "historia". Es lo que después permite verificar:
    si dos medios independientes o el propio laboratorio cuentan lo mismo.
    """
    orden = sorted(items, key=lambda i: ({"oficial": 0, "medio": 1, "comunidad": 2}[i["tipo"]],))
    grupos = []
    for item in orden:
        pal = palabras(item["titulo"])
        mejor, mejor_sim = None, 0.0
        for g in grupos:
            sim = max(similitud(pal, palabras(o["titulo"])) for o in g["items"])
            if sim > mejor_sim:
                mejor, mejor_sim = g, sim
        if mejor is not None and mejor_sim >= umbral:
            mejor["items"].append(item)
        else:
            grupos.append({"items": [item]})
    for n, g in enumerate(grupos, 1):
        g["id"] = f"h{n:02d}"
        g["principal"] = g["items"][0]
    return grupos
